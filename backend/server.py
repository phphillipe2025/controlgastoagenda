from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import jwt
from passlib.context import CryptContext
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

# LLM Setup
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    description: str
    amount: float
    category: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: Optional[str] = None

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None

class AIInsight(BaseModel):
    type: str  # "categorization", "suggestion", "prediction"
    message: str
    data: dict

# Helper function to prepare data for MongoDB
def prepare_for_mongo(data):
    if isinstance(data, dict):
        prepared = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                prepared[key] = value.isoformat()
            else:
                prepared[key] = value
        return prepared
    return data

# Helper function to parse data from MongoDB
def parse_from_mongo(data):
    if isinstance(data, dict):
        parsed = {}
        for key, value in data.items():
            # Skip MongoDB's _id field to avoid ObjectId serialization issues
            if key == '_id':
                continue
            elif key.endswith('_at') or key == 'date':
                if isinstance(value, str):
                    try:
                        parsed[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        parsed[key] = value
                else:
                    parsed[key] = value
            else:
                parsed[key] = value
        return parsed
    return data

# Authentication endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    user_dict = prepare_for_mongo(user.dict())
    await db.users.insert_one(user_dict)
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

# AI Integration functions
async def categorize_expense_with_ai(description: str, amount: float) -> str:
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"categorize_{uuid.uuid4()}",
            system_message="Você é um assistente financeiro especializado em categorizar gastos. Responda APENAS com uma categoria em português, sem explicações."
        ).with_model("openai", "gpt-5")
        
        user_message = UserMessage(
            text=f"Categorize este gasto: '{description}' no valor de R$ {amount:.2f}. Escolha UMA categoria entre: Alimentação, Transporte, Moradia, Saúde, Educação, Entretenimento, Vestuário, Tecnologia, Serviços, Outros"
        )
        
        response = await chat.send_message(user_message)
        return response.strip()
    except Exception as e:
        logging.error(f"Error categorizing expense: {e}")
        return "Outros"

async def get_financial_insights(expenses: List[dict]) -> str:
    try:
        total_spent = sum(exp["amount"] for exp in expenses)
        categories = {}
        for exp in expenses:
            cat = exp["category"]
            categories[cat] = categories.get(cat, 0) + exp["amount"]
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"insights_{uuid.uuid4()}",
            system_message="Você é um consultor financeiro. Forneça insights úteis e sugestões de economia baseados nos dados dos gastos."
        ).with_model("openai", "gpt-5")
        
        user_message = UserMessage(
            text=f"Analise estes gastos: Total gasto: R$ {total_spent:.2f}. Gastos por categoria: {json.dumps(categories, ensure_ascii=False)}. Forneça insights e sugestões de economia."
        )
        
        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        logging.error(f"Error generating insights: {e}")
        return "Não foi possível gerar insights no momento."

async def predict_future_expenses(expenses: List[dict]) -> str:
    try:
        if len(expenses) < 3:
            return "Adicione mais gastos para obter previsões precisas."
        
        monthly_avg = sum(exp["amount"] for exp in expenses[-30:]) / min(30, len(expenses))
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"prediction_{uuid.uuid4()}",
            system_message="Você é um analista financeiro. Faça previsões realistas de gastos futuros baseado no histórico."
        ).with_model("openai", "gpt-5")
        
        user_message = UserMessage(
            text=f"Com base nos gastos recentes, a média diária é R$ {monthly_avg:.2f}. Histórico: {json.dumps([{'desc': e['description'], 'valor': e['amount'], 'categoria': e['category']} for e in expenses[-10:]], ensure_ascii=False)}. Faça previsões para os próximos meses."
        )
        
        response = await chat.send_message(user_message)
        return response
    except Exception as e:
        logging.error(f"Error predicting expenses: {e}")
        return "Não foi possível gerar previsões no momento."

# Expense endpoints
@api_router.post("/expenses", response_model=Expense)
async def create_expense(expense_data: ExpenseCreate, current_user: dict = Depends(get_current_user)):
    category = expense_data.category
    if not category:
        category = await categorize_expense_with_ai(expense_data.description, expense_data.amount)
    
    expense = Expense(
        user_id=current_user["id"],
        description=expense_data.description,
        amount=expense_data.amount,
        category=category
    )
    
    expense_dict = prepare_for_mongo(expense.dict())
    await db.expenses.insert_one(expense_dict)
    return expense

@api_router.get("/expenses", response_model=List[Expense])
async def get_expenses(current_user: dict = Depends(get_current_user)):
    expenses = await db.expenses.find({"user_id": current_user["id"]}).sort("date", -1).to_list(1000)
    return [Expense(**parse_from_mongo(expense)) for expense in expenses]

@api_router.put("/expenses/{expense_id}", response_model=Expense)
async def update_expense(expense_id: str, expense_data: ExpenseUpdate, current_user: dict = Depends(get_current_user)):
    expense = await db.expenses.find_one({"id": expense_id, "user_id": current_user["id"]})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    update_data = {k: v for k, v in expense_data.dict().items() if v is not None}
    if update_data:
        await db.expenses.update_one({"id": expense_id}, {"$set": update_data})
        expense.update(update_data)
    
    return Expense(**parse_from_mongo(expense))

@api_router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.expenses.delete_one({"id": expense_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}

# AI endpoints
@api_router.get("/ai/insights")
async def get_insights(current_user: dict = Depends(get_current_user)):
    expenses = await db.expenses.find({"user_id": current_user["id"]}).to_list(1000)
    if not expenses:
        return {"message": "Adicione alguns gastos para receber insights personalizados!"}
    
    insights = await get_financial_insights(expenses)
    return {"insights": insights}

@api_router.get("/ai/predictions")
async def get_predictions(current_user: dict = Depends(get_current_user)):
    expenses = await db.expenses.find({"user_id": current_user["id"]}).to_list(1000)
    predictions = await predict_future_expenses(expenses)
    return {"predictions": predictions}

# Dashboard data
@api_router.get("/dashboard")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    expenses = await db.expenses.find({"user_id": current_user["id"]}).to_list(1000)
    
    total_spent = sum(exp["amount"] for exp in expenses)
    categories = {}
    monthly_data = {}
    
    for exp in expenses:
        # Categories
        cat = exp["category"]
        categories[cat] = categories.get(cat, 0) + exp["amount"]
        
        # Monthly data
        date_obj = exp["date"]
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        month_key = date_obj.strftime("%Y-%m")
        monthly_data[month_key] = monthly_data.get(month_key, 0) + exp["amount"]
    
    # Parse recent expenses to remove ObjectIds
    recent_expenses = []
    for exp in expenses[:5]:
        parsed_exp = parse_from_mongo(exp)
        recent_expenses.append(parsed_exp)
    
    return {
        "total_spent": total_spent,
        "total_expenses": len(expenses),
        "categories": categories,
        "monthly_data": monthly_data,
        "recent_expenses": recent_expenses
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()