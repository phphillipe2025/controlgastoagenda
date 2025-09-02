import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Badge } from "./components/ui/badge";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Separator } from "./components/ui/separator";
import { toast, Toaster } from "sonner";
import { 
  PlusCircle, 
  DollarSign, 
  TrendingUp, 
  Brain, 
  CreditCard, 
  BarChart3,
  Trash2,
  Edit,
  Sparkles,
  Target,
  Calendar,
  User,
  LogOut
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configuração do axios
axios.defaults.headers.common['Authorization'] = '';

function App() {
  const [user, setUser] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [dashboardData, setDashboardData] = useState({});
  const [insights, setInsights] = useState("");
  const [predictions, setPredictions] = useState("");
  const [loading, setLoading] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  
  // Form states
  const [authForm, setAuthForm] = useState({
    username: "",
    email: "",
    password: ""
  });
  
  const [expenseForm, setExpenseForm] = useState({
    description: "",
    amount: "",
    category: ""
  });

  // Check if user is logged in
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      loadUserData();
    }
  }, []);

  const loadUserData = async () => {
    try {
      await Promise.all([
        loadExpenses(),
        loadDashboardData(),
        loadInsights()
      ]);
    } catch (error) {
      console.error('Error loading user data:', error);
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const loadExpenses = async () => {
    try {
      const response = await axios.get(`${API}/expenses`);
      setExpenses(response.data);
    } catch (error) {
      console.error('Error loading expenses:', error);
    }
  };

  const loadDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    }
  };

  const loadInsights = async () => {
    try {
      const [insightsRes, predictionsRes] = await Promise.all([
        axios.get(`${API}/ai/insights`),
        axios.get(`${API}/ai/predictions`)
      ]);
      setInsights(insightsRes.data.insights || insightsRes.data.message);
      setPredictions(predictionsRes.data.predictions);
    } catch (error) {
      console.error('Error loading AI insights:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const endpoint = authMode === "login" ? "/auth/login" : "/auth/register";
      const data = authMode === "login" 
        ? { username: authForm.username, password: authForm.password }
        : authForm;
      
      const response = await axios.post(`${API}${endpoint}`, data);
      const token = response.data.access_token;
      
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUser({ username: authForm.username });
      
      // Reset form
      setAuthForm({ username: "", email: "", password: "" });
      
      // Load user data
      await loadUserData();
      
      toast.success(authMode === "login" ? "Login realizado com sucesso!" : "Conta criada com sucesso!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro na autenticação");
    } finally {
      setLoading(false);
    }
  };

  const handleAddExpense = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const data = {
        description: expenseForm.description,
        amount: parseFloat(expenseForm.amount),
        category: expenseForm.category || null
      };
      
      await axios.post(`${API}/expenses`, data);
      
      // Reset form
      setExpenseForm({ description: "", amount: "", category: "" });
      
      // Reload data
      await loadUserData();
      
      toast.success("Gasto adicionado com sucesso!");
    } catch (error) {
      toast.error("Erro ao adicionar gasto");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteExpense = async (expenseId) => {
    try {
      await axios.delete(`${API}/expenses/${expenseId}`);
      await loadUserData();
      toast.success("Gasto removido com sucesso!");
    } catch (error) {
      toast.error("Erro ao remover gasto");
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    axios.defaults.headers.common['Authorization'] = '';
    setUser(null);
    setExpenses([]);
    setDashboardData({});
    setInsights("");
    setPredictions("");
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Alimentação': 'bg-green-100 text-green-800',
      'Transporte': 'bg-blue-100 text-blue-800',
      'Moradia': 'bg-purple-100 text-purple-800',
      'Saúde': 'bg-red-100 text-red-800',
      'Educação': 'bg-yellow-100 text-yellow-800',
      'Entretenimento': 'bg-pink-100 text-pink-800',
      'Vestuário': 'bg-indigo-100 text-indigo-800',
      'Tecnologia': 'bg-cyan-100 text-cyan-800',
      'Serviços': 'bg-orange-100 text-orange-800',
      'Outros': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  // If not logged in, show auth form
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
        <div className="w-full max-w-md p-8">
          <Card className="shadow-xl border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="text-center pb-8">
              <div className="mx-auto w-16 h-16 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mb-4">
                <DollarSign className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl font-bold text-gray-900">
                Controle Financeiro IA
              </CardTitle>
              <CardDescription className="text-gray-600">
                Gerencie seus gastos com inteligência artificial
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
                <button
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                    authMode === "login"
                      ? "bg-white text-gray-900 shadow-sm"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                  onClick={() => setAuthMode("login")}
                >
                  Entrar
                </button>
                <button
                  className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                    authMode === "register"
                      ? "bg-white text-gray-900 shadow-sm"
                      : "text-gray-600 hover:text-gray-900"
                  }`}
                  onClick={() => setAuthMode("register")}
                >
                  Cadastrar
                </button>
              </div>
              
              <form onSubmit={handleAuth} className="space-y-4">
                <div>
                  <Label htmlFor="username">Usuário</Label>
                  <Input
                    id="username"
                    type="text"
                    value={authForm.username}
                    onChange={(e) => setAuthForm({...authForm, username: e.target.value})}
                    required
                    className="mt-1"
                  />
                </div>
                
                {authMode === "register" && (
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={authForm.email}
                      onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                      required
                      className="mt-1"
                    />
                  </div>
                )}
                
                <div>
                  <Label htmlFor="password">Senha</Label>
                  <Input
                    id="password"
                    type="password"
                    value={authForm.password}
                    onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
                    required
                    className="mt-1"
                  />
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700"
                  disabled={loading}
                >
                  {loading ? "Processando..." : (authMode === "login" ? "Entrar" : "Cadastrar")}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
        <Toaster position="top-right" />
      </div>
    );
  }

  // Main dashboard
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50">
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Controle Financeiro</h1>
              <p className="text-gray-600">Bem-vindo, {user.username}!</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Dialog>
              <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700">
                  <PlusCircle className="w-4 h-4 mr-2" />
                  Novo Gasto
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Adicionar Novo Gasto</DialogTitle>
                  <DialogDescription>
                    A IA irá categorizar automaticamente seu gasto
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleAddExpense} className="space-y-4">
                  <div>
                    <Label htmlFor="description">Descrição</Label>
                    <Input
                      id="description"
                      value={expenseForm.description}
                      onChange={(e) => setExpenseForm({...expenseForm, description: e.target.value})}
                      placeholder="Ex: Almoço no restaurante"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="amount">Valor</Label>
                    <Input
                      id="amount"
                      type="number"
                      step="0.01"
                      value={expenseForm.amount}
                      onChange={(e) => setExpenseForm({...expenseForm, amount: e.target.value})}
                      placeholder="0,00"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="category">Categoria (opcional)</Label>
                    <Input
                      id="category"
                      value={expenseForm.category}
                      onChange={(e) => setExpenseForm({...expenseForm, category: e.target.value})}
                      placeholder="Deixe vazio para categorização automática"
                    />
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button type="submit" disabled={loading} className="flex-1">
                      {loading ? "Adicionando..." : "Adicionar Gasto"}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
            
            <Button variant="outline" onClick={logout}>
              <LogOut className="w-4 h-4 mr-2" />
              Sair
            </Button>
          </div>
        </div>

        {/* Dashboard Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Gasto</CardTitle>
              <DollarSign className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData.total_spent || 0)}
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total de Gastos</CardTitle>
              <CreditCard className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {dashboardData.total_expenses || 0}
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Categorias</CardTitle>
              <BarChart3 className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {Object.keys(dashboardData.categories || {}).length}
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">IA Ativa</CardTitle>
              <Brain className="h-4 w-4 text-pink-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-600">
                <Sparkles className="h-6 w-6" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="expenses" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-96">
            <TabsTrigger value="expenses">Gastos</TabsTrigger>
            <TabsTrigger value="insights">Insights IA</TabsTrigger>
            <TabsTrigger value="analytics">Análises</TabsTrigger>
          </TabsList>
          
          <TabsContent value="expenses" className="space-y-6">
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  Seus Gastos Recentes
                </CardTitle>
              </CardHeader>
              <CardContent>
                {expenses.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500 mb-4">Nenhum gasto registrado ainda</p>
                    <p className="text-sm text-gray-400">Comece adicionando seu primeiro gasto!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {expenses.map((expense) => (
                      <div key={expense.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <p className="font-medium text-gray-900">{expense.description}</p>
                            <Badge className={getCategoryColor(expense.category)}>
                              {expense.category}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-500">{formatDate(expense.date)}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <p className="text-lg font-semibold text-gray-900">
                            {formatCurrency(expense.amount)}
                          </p>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleDeleteExpense(expense.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="insights" className="space-y-6">
            <div className="grid gap-6">
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-emerald-600" />
                    Insights Financeiros
                  </CardTitle>
                  <CardDescription>
                    Análises inteligentes dos seus gastos
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {insights ? (
                    <div className="prose prose-sm max-w-none">
                      <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{insights}</p>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Brain className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500">Carregando insights...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
              
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                    Previsões Futuras
                  </CardTitle>
                  <CardDescription>
                    Projeções baseadas no seu histórico
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {predictions ? (
                    <div className="prose prose-sm max-w-none">
                      <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{predictions}</p>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500">Carregando previsões...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          <TabsContent value="analytics" className="space-y-6">
            <div className="grid gap-6">
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    Gastos por Categoria
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {Object.keys(dashboardData.categories || {}).length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-500">Nenhuma categoria encontrada</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {Object.entries(dashboardData.categories || {}).map(([category, amount]) => (
                        <div key={category} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <Badge className={getCategoryColor(category)}>
                              {category}
                            </Badge>
                          </div>
                          <p className="font-semibold text-gray-900">
                            {formatCurrency(amount)}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;