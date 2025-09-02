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
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import tempfile

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
    salary: Optional[float] = 0.0
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

class SalaryUpdate(BaseModel):
    salary: float

class InstallmentExpense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    description: str
    total_amount: float
    installments: int
    current_installment: int = 1
    monthly_amount: float
    category: str
    start_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InstallmentExpenseCreate(BaseModel):
    description: str
    total_amount: float
    installments: int
    category: Optional[str] = None

class PeriodFilter(BaseModel):
    start_date: datetime
    end_date: datetime

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

# Salary endpoints
@api_router.put("/user/salary")
async def update_salary(salary_data: SalaryUpdate, current_user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"id": current_user["id"]}, 
        {"$set": {"salary": salary_data.salary}}
    )
    return {"message": "Salário atualizado com sucesso", "salary": salary_data.salary}

@api_router.get("/user/salary")
async def get_salary(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["id"]})
    return {"salary": user.get("salary", 0.0)}

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

# Installment expenses endpoints
@api_router.post("/installment-expenses", response_model=InstallmentExpense)
async def create_installment_expense(expense_data: InstallmentExpenseCreate, current_user: dict = Depends(get_current_user)):
    category = expense_data.category
    if not category:
        category = await categorize_expense_with_ai(expense_data.description, expense_data.total_amount)
    
    monthly_amount = expense_data.total_amount / expense_data.installments
    
    installment_expense = InstallmentExpense(
        user_id=current_user["id"],
        description=expense_data.description,
        total_amount=expense_data.total_amount,
        installments=expense_data.installments,
        monthly_amount=monthly_amount,
        category=category
    )
    
    # Create the installment expense record
    installment_dict = prepare_for_mongo(installment_expense.dict())
    await db.installment_expenses.insert_one(installment_dict)
    
    # Create individual expenses for each month
    current_date = datetime.now(timezone.utc)
    for i in range(expense_data.installments):
        # Calculate the future date for each installment
        future_year = current_date.year
        future_month = current_date.month + i
        
        # Handle month overflow
        while future_month > 12:
            future_month -= 12
            future_year += 1
        
        expense_date = current_date.replace(year=future_year, month=future_month)
        
        expense = Expense(
            user_id=current_user["id"],
            description=f"{expense_data.description} ({i+1}/{expense_data.installments})",
            amount=monthly_amount,
            category=category,
            date=expense_date
        )
        
        expense_dict = prepare_for_mongo(expense.dict())
        await db.expenses.insert_one(expense_dict)
    
    return installment_expense

@api_router.get("/installment-expenses", response_model=List[InstallmentExpense])
async def get_installment_expenses(current_user: dict = Depends(get_current_user)):
    installments = await db.installment_expenses.find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(1000)
    return [InstallmentExpense(**parse_from_mongo(installment)) for installment in installments]

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

# Period reports
@api_router.get("/reports/period")
async def get_period_report(start_date: str, end_date: str, current_user: dict = Depends(get_current_user)):
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
    
    # Get expenses in the period
    expenses = await db.expenses.find({
        "user_id": current_user["id"],
        "date": {"$gte": start_dt.isoformat(), "$lte": end_dt.isoformat()}
    }).to_list(1000)
    
    total_spent = sum(exp["amount"] for exp in expenses)
    categories = {}
    daily_data = {}
    
    for exp in expenses:
        # Categories
        cat = exp["category"]
        categories[cat] = categories.get(cat, 0) + exp["amount"]
        
        # Daily data
        date_obj = exp["date"]
        if isinstance(date_obj, str):
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        day_key = date_obj.strftime("%Y-%m-%d")
        daily_data[day_key] = daily_data.get(day_key, 0) + exp["amount"]
    
    return {
        "period": {"start": start_date, "end": end_date},
        "total_spent": total_spent,
        "total_expenses": len(expenses),
        "categories": categories,
        "daily_data": daily_data,
        "expenses": [parse_from_mongo(exp) for exp in expenses]
    }

# PDF Export
@api_router.get("/reports/export-pdf")
async def export_period_report_pdf(start_date: str, end_date: str, current_user: dict = Depends(get_current_user)):
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")
    
    # Get report data
    expenses = await db.expenses.find({
        "user_id": current_user["id"],
        "date": {"$gte": start_dt.isoformat(), "$lte": end_dt.isoformat()}
    }).to_list(1000)
    
    # Get user data
    user = await db.users.find_one({"id": current_user["id"]})
    
    # Create PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        doc = SimpleDocTemplate(tmp_file.name, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        title = Paragraph(f"Relatório Financeiro - {start_dt.strftime('%d/%m/%Y')} a {end_dt.strftime('%d/%m/%Y')}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Summary
        total_spent = sum(exp["amount"] for exp in expenses)
        user_salary = user.get("salary", 0.0)
        balance = user_salary - total_spent
        
        summary_data = [
            ["Salário Mensal:", f"R$ {user_salary:.2f}"],
            ["Total de Gastos:", f"R$ {total_spent:.2f}"],
            ["Saldo:", f"R$ {balance:.2f}"],
            ["Número de Transações:", str(len(expenses))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 12))
        
        # Expenses table
        if expenses:
            elements.append(Paragraph("Detalhes dos Gastos:", styles['Heading2']))
            elements.append(Spacer(1, 12))
            
            expense_data = [["Data", "Descrição", "Categoria", "Valor"]]
            for exp in expenses:
                date_obj = exp["date"]
                if isinstance(date_obj, str):
                    date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
                
                expense_data.append([
                    date_obj.strftime('%d/%m/%Y'),
                    exp["description"][:30] + "..." if len(exp["description"]) > 30 else exp["description"],
                    exp["category"],
                    f"R$ {exp['amount']:.2f}"
                ])
            
            expense_table = Table(expense_data, colWidths=[1.2*inch, 2.5*inch, 1.5*inch, 1.2*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            elements.append(expense_table)
        
        doc.build(elements)
        
        return FileResponse(
            tmp_file.name,
            media_type='application/pdf',
            filename=f"relatorio_financeiro_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.pdf"
        )

# Dashboard data
@api_router.get("/dashboard")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    # Get current month expenses
    current_date = datetime.now(timezone.utc)
    start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_month = (start_of_month.replace(month=start_of_month.month + 1) if start_of_month.month < 12 
                   else start_of_month.replace(year=start_of_month.year + 1, month=1))
    
    # All expenses
    all_expenses = await db.expenses.find({"user_id": current_user["id"]}).to_list(1000)
    
    # Current month expenses
    current_month_expenses = await db.expenses.find({
        "user_id": current_user["id"],
        "date": {
            "$gte": start_of_month.isoformat(),
            "$lt": end_of_month.isoformat()
        }
    }).to_list(1000)
    
    # Get user salary
    user = await db.users.find_one({"id": current_user["id"]})
    salary = user.get("salary", 0.0)
    
    total_spent = sum(exp["amount"] for exp in all_expenses)
    current_month_spent = sum(exp["amount"] for exp in current_month_expenses)
    current_balance = salary - current_month_spent
    
    categories = {}
    monthly_data = {}
    
    for exp in all_expenses:
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
    for exp in all_expenses[:5]:
        parsed_exp = parse_from_mongo(exp)
        recent_expenses.append(parsed_exp)
    
    return {
        "total_spent": total_spent,
        "current_month_spent": current_month_spent,
        "salary": salary,
        "current_balance": current_balance,
        "total_expenses": len(all_expenses),
        "categories": categories,
        "monthly_data": monthly_data,
        "recent_expenses": recent_expenses
    }

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Expense Tracker API is running!", "status": "healthy"}

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running successfully"}

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