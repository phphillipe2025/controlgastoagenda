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
import { Textarea } from "./components/ui/textarea";
import { toast, Toaster } from "sonner";
import { Calendar } from "./components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
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
  Calendar as CalendarIcon,
  User,
  LogOut,
  Download,
  Wallet,
  TrendingDown,
  Repeat,
  FileText,
  Clock,
  MapPin,
  CheckCircle,
  AlertCircle,
  XCircle
} from "lucide-react";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configuração do axios
axios.defaults.headers.common['Authorization'] = '';

function App() {
  const [user, setUser] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [installmentExpenses, setInstallmentExpenses] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [calendarData, setCalendarData] = useState(null);
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

  const [installmentForm, setInstallmentForm] = useState({
    description: "",
    total_amount: "",
    installments: "",
    category: ""
  });

  const [salaryForm, setSalaryForm] = useState({
    salary: ""
  });

  const [appointmentForm, setAppointmentForm] = useState({
    title: "",
    description: "",
    date: new Date(),
    time: "",
    location: ""
  });

  // Date picker states
  const [startDate, setStartDate] = useState(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const [endDate, setEndDate] = useState(new Date());
  const [periodReport, setPeriodReport] = useState(null);

  // Modal states
  const [isSalaryModalOpen, setIsSalaryModalOpen] = useState(false);
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);
  const [isInstallmentModalOpen, setIsInstallmentModalOpen] = useState(false);
  const [isAppointmentModalOpen, setIsAppointmentModalOpen] = useState(false);

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
        loadInstallmentExpenses(),
        loadAppointments(),
        loadCalendarData(),
        loadDashboardData(),
        loadInsights(),
        loadSalary()
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

  const loadInstallmentExpenses = async () => {
    try {
      const response = await axios.get(`${API}/installment-expenses`);
      setInstallmentExpenses(response.data);
    } catch (error) {
      console.error('Error loading installment expenses:', error);
    }
  };

  const loadAppointments = async () => {
    try {
      const response = await axios.get(`${API}/appointments`);
      setAppointments(response.data);
    } catch (error) {
      console.error('Error loading appointments:', error);
    }
  };

  const loadCalendarData = async () => {
    try {
      const response = await axios.get(`${API}/calendar/spending`);
      setCalendarData(response.data);
    } catch (error) {
      console.error('Error loading calendar data:', error);
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

  const loadSalary = async () => {
    try {
      const response = await axios.get(`${API}/user/salary`);
      setSalaryForm({ salary: response.data.salary.toString() });
    } catch (error) {
      console.error('Error loading salary:', error);
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
      setIsExpenseModalOpen(false);
      
      // Reload data
      await loadUserData();
      
      toast.success("Gasto adicionado com sucesso!");
    } catch (error) {
      toast.error("Erro ao adicionar gasto");
    } finally {
      setLoading(false);
    }
  };

  const handleAddInstallmentExpense = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const data = {
        description: installmentForm.description,
        total_amount: parseFloat(installmentForm.total_amount),
        installments: parseInt(installmentForm.installments),
        category: installmentForm.category || null
      };
      
      await axios.post(`${API}/installment-expenses`, data);
      
      // Reset form
      setInstallmentForm({ description: "", total_amount: "", installments: "", category: "" });
      setIsInstallmentModalOpen(false);
      
      // Reload data
      await loadUserData();
      
      toast.success("Gasto parcelado adicionado com sucesso!");
    } catch (error) {
      toast.error("Erro ao adicionar gasto parcelado");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSalary = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.put(`${API}/user/salary`, {
        salary: parseFloat(salaryForm.salary)
      });
      
      setIsSalaryModalOpen(false);
      await loadUserData();
      
      toast.success("Salário atualizado com sucesso!");
    } catch (error) {
      toast.error("Erro ao atualizar salário");
    } finally {
      setLoading(false);
    }
  };

  const handleAddAppointment = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const data = {
        title: appointmentForm.title,
        description: appointmentForm.description,
        date: appointmentForm.date.toISOString(),
        time: appointmentForm.time,
        location: appointmentForm.location
      };
      
      await axios.post(`${API}/appointments`, data);
      
      // Reset form
      setAppointmentForm({
        title: "",
        description: "",
        date: new Date(),
        time: "",
        location: ""
      });
      setIsAppointmentModalOpen(false);
      
      // Reload data
      await loadAppointments();
      
      toast.success("Compromisso agendado com sucesso!");
    } catch (error) {
      toast.error("Erro ao agendar compromisso");
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

  const handleDeleteAppointment = async (appointmentId) => {
    try {
      await axios.delete(`${API}/appointments/${appointmentId}`);
      await loadAppointments();
      toast.success("Compromisso removido com sucesso!");
    } catch (error) {
      toast.error("Erro ao remover compromisso");
    }
  };

  const loadPeriodReport = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/reports/period`, {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      });
      setPeriodReport(response.data);
    } catch (error) {
      toast.error("Erro ao carregar relatório");
    } finally {
      setLoading(false);
    }
  };

  const exportPDF = async () => {
    try {
      const response = await axios.get(`${API}/reports/export-pdf`, {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `relatorio_${format(startDate, 'ddMMyyyy')}_${format(endDate, 'ddMMyyyy')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("PDF exportado com sucesso!");
    } catch (error) {
      toast.error("Erro ao exportar PDF");
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    axios.defaults.headers.common['Authorization'] = '';
    setUser(null);
    setExpenses([]);
    setInstallmentExpenses([]);
    setAppointments([]);
    setCalendarData(null);
    setDashboardData({});
    setInsights("");
    setPredictions("");
    setPeriodReport(null);
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

  const formatTime = (timeString) => {
    return timeString.substring(0, 5); // HH:MM
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

  const getDayStatusColor = (day) => {
    if (!day) return 'bg-gray-100';
    
    if (day.is_past) {
      return day.spent > 0 ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-600';
    } else if (day.is_today) {
      return day.available > 0 ? 'bg-blue-100 text-blue-800' : 'bg-red-100 text-red-800';
    } else {
      return day.available > 0 ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800';
    }
  };

  const getDayStatusIcon = (day) => {
    if (!day) return null;
    
    if (day.is_past) {
      return day.spent > 0 ? <XCircle className="w-3 h-3" /> : <CheckCircle className="w-3 h-3" />;
    } else if (day.is_today) {
      return <AlertCircle className="w-3 h-3" />;
    } else {
      return day.available > 0 ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />;
    }
  };

  const getAppointmentsForDay = (day) => {
    if (!calendarData || !appointments) return [];
    
    const dayDate = new Date(calendarData.year, calendarData.month - 1, day);
    return appointments.filter(apt => {
      const aptDate = new Date(apt.date);
      return aptDate.toDateString() === dayDate.toDateString();
    });
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
          
          <div className="flex items-center gap-3 flex-wrap">
            <Dialog open={isSalaryModalOpen} onOpenChange={setIsSalaryModalOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="gap-2">
                  <Wallet className="w-4 h-4" />
                  Definir Salário
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Definir Salário Mensal</DialogTitle>
                  <DialogDescription>
                    Informe seu salário para calcular o saldo disponível
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleUpdateSalary} className="space-y-4">
                  <div>
                    <Label htmlFor="salary">Salário Mensal</Label>
                    <Input
                      id="salary"
                      type="number"
                      step="0.01"
                      value={salaryForm.salary}
                      onChange={(e) => setSalaryForm({salary: e.target.value})}
                      placeholder="0,00"
                      required
                    />
                  </div>
                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? "Salvando..." : "Salvar Salário"}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>

            <Dialog open={isExpenseModalOpen} onOpenChange={setIsExpenseModalOpen}>
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
                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? "Adicionando..." : "Adicionar Gasto"}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>

            <Dialog open={isInstallmentModalOpen} onOpenChange={setIsInstallmentModalOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="gap-2">
                  <Repeat className="w-4 h-4" />
                  Gasto Parcelado
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Adicionar Gasto Parcelado</DialogTitle>
                  <DialogDescription>
                    Crie parcelas automáticas para os próximos meses
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleAddInstallmentExpense} className="space-y-4">
                  <div>
                    <Label htmlFor="inst_description">Descrição</Label>
                    <Input
                      id="inst_description"
                      value={installmentForm.description}
                      onChange={(e) => setInstallmentForm({...installmentForm, description: e.target.value})}
                      placeholder="Ex: Compra no cartão"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="total_amount">Valor Total</Label>
                    <Input
                      id="total_amount"
                      type="number"
                      step="0.01"
                      value={installmentForm.total_amount}
                      onChange={(e) => setInstallmentForm({...installmentForm, total_amount: e.target.value})}
                      placeholder="0,00"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="installments">Número de Parcelas</Label>
                    <Input
                      id="installments"
                      type="number"
                      min="2"
                      max="48"
                      value={installmentForm.installments}
                      onChange={(e) => setInstallmentForm({...installmentForm, installments: e.target.value})}
                      placeholder="12"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="inst_category">Categoria (opcional)</Label>
                    <Input
                      id="inst_category"
                      value={installmentForm.category}
                      onChange={(e) => setInstallmentForm({...installmentForm, category: e.target.value})}
                      placeholder="Deixe vazio para categorização automática"
                    />
                  </div>
                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? "Adicionando..." : "Adicionar Gasto Parcelado"}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>

            <Dialog open={isAppointmentModalOpen} onOpenChange={setIsAppointmentModalOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="gap-2">
                  <CalendarIcon className="w-4 h-4" />
                  Novo Compromisso
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Agendar Compromisso</DialogTitle>
                  <DialogDescription>
                    Adicione um novo compromisso à sua agenda
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleAddAppointment} className="space-y-4">
                  <div>
                    <Label htmlFor="apt_title">Título</Label>
                    <Input
                      id="apt_title"
                      value={appointmentForm.title}
                      onChange={(e) => setAppointmentForm({...appointmentForm, title: e.target.value})}
                      placeholder="Ex: Reunião importante"
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="apt_description">Descrição</Label>
                    <Textarea
                      id="apt_description"
                      value={appointmentForm.description}
                      onChange={(e) => setAppointmentForm({...appointmentForm, description: e.target.value})}
                      placeholder="Detalhes do compromisso"
                      rows={3}
                    />
                  </div>
                  <div>
                    <Label>Data</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button variant="outline" className="w-full justify-start text-left font-normal">
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {appointmentForm.date ? format(appointmentForm.date, "PPP", { locale: ptBR }) : "Selecione a data"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar 
                          mode="single" 
                          selected={appointmentForm.date} 
                          onSelect={(date) => setAppointmentForm({...appointmentForm, date: date || new Date()})} 
                        />
                      </PopoverContent>
                    </Popover>
                  </div>
                  <div>
                    <Label htmlFor="apt_time">Horário</Label>
                    <Input
                      id="apt_time"
                      type="time"
                      value={appointmentForm.time}
                      onChange={(e) => setAppointmentForm({...appointmentForm, time: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="apt_location">Local (opcional)</Label>
                    <Input
                      id="apt_location"
                      value={appointmentForm.location}
                      onChange={(e) => setAppointmentForm({...appointmentForm, location: e.target.value})}
                      placeholder="Ex: Escritório, Casa, Online"
                    />
                  </div>
                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? "Agendando..." : "Agendar Compromisso"}
                  </Button>
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Salário</CardTitle>
              <Wallet className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData.salary || 0)}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Saldo Atual</CardTitle>
              <TrendingUp className="h-4 w-4 text-emerald-600" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${(dashboardData.current_balance || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                {formatCurrency(dashboardData.current_balance || 0)}
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Gasto do Mês</CardTitle>
              <TrendingDown className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData.current_month_spent || 0)}
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total de Gastos</CardTitle>
              <CreditCard className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {dashboardData.total_expenses || 0}
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
          <TabsList className="grid w-full grid-cols-6 lg:w-[720px]">
            <TabsTrigger value="expenses">Gastos</TabsTrigger>
            <TabsTrigger value="calendar">Calendário</TabsTrigger>
            <TabsTrigger value="installments">Parcelados</TabsTrigger>
            <TabsTrigger value="insights">Insights IA</TabsTrigger>
            <TabsTrigger value="analytics">Análises</TabsTrigger>
            <TabsTrigger value="reports">Relatórios</TabsTrigger>
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

          <TabsContent value="calendar" className="space-y-6">
            <div className="grid gap-6">
              {/* Calendar Summary */}
              {calendarData && (
                <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CalendarIcon className="w-5 h-5" />
                      Calendário Inteligente - {new Date(calendarData.year, calendarData.month - 1).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}
                    </CardTitle>
                    <CardDescription>
                      Veja quanto você pode gastar por dia baseado no seu saldo
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <p className="text-sm text-gray-600">Dias Restantes</p>
                        <p className="text-2xl font-bold text-blue-600">{calendarData.days_remaining}</p>
                      </div>
                      <div className="text-center p-4 bg-emerald-50 rounded-lg">
                        <p className="text-sm text-gray-600">Saldo Disponível</p>
                        <p className="text-2xl font-bold text-emerald-600">{formatCurrency(calendarData.remaining_balance)}</p>
                      </div>
                      <div className="text-center p-4 bg-orange-50 rounded-lg">
                        <p className="text-sm text-gray-600">Por Dia</p>
                        <p className="text-2xl font-bold text-orange-600">{formatCurrency(calendarData.daily_available)}</p>
                      </div>
                    </div>

                    {/* Calendar Grid */}
                    <div className="grid grid-cols-7 gap-2 mb-4">
                      {['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'].map(day => (
                        <div key={day} className="text-center font-medium text-gray-600 py-2">
                          {day}
                        </div>
                      ))}
                    </div>

                    <div className="grid grid-cols-7 gap-2">
                      {calendarData.calendar_data.map((day) => {
                        const dayAppointments = getAppointmentsForDay(day.day);
                        return (
                          <div
                            key={day.day}
                            className={`min-h-[100px] p-2 rounded-lg border ${getDayStatusColor(day)} transition-all hover:shadow-md`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium">{day.day}</span>
                              {getDayStatusIcon(day)}
                            </div>
                            
                            <div className="text-xs space-y-1">
                              {day.is_past && day.spent > 0 && (
                                <div className="font-medium">
                                  Gasto: {formatCurrency(day.spent)}
                                </div>
                              )}
                              {(day.is_today || day.is_future) && day.available > 0 && (
                                <div className="font-medium">
                                  Disponível: {formatCurrency(day.available)}
                                </div>
                              )}
                              
                              {/* Appointments */}
                              {dayAppointments.map((apt) => (
                                <div key={apt.id} className="bg-white/50 rounded px-1 py-0.5 text-xs">
                                  <div className="flex items-center gap-1">
                                    <Clock className="w-2 h-2" />
                                    {formatTime(apt.time)}
                                  </div>
                                  <div className="truncate">{apt.title}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Legend */}
                    <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-green-100 border border-green-200 rounded"></div>
                        <span>Pode gastar</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded"></div>
                        <span>Hoje</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-red-100 border border-red-200 rounded"></div>
                        <span>Já gastou</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-orange-100 border border-orange-200 rounded"></div>
                        <span>Sem orçamento</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Appointments List */}
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    Próximos Compromissos
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {appointments.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-500 mb-4">Nenhum compromisso agendado</p>
                      <p className="text-sm text-gray-400">Clique em "Novo Compromisso" para agendar!</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {appointments.slice(0, 5).map((appointment) => (
                        <div key={appointment.id} className="flex items-start justify-between p-4 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="font-medium text-gray-900">{appointment.title}</h3>
                              <Badge variant="outline" className="text-xs">
                                {formatDate(appointment.date)} {formatTime(appointment.time)}
                              </Badge>
                            </div>
                            {appointment.description && (
                              <p className="text-sm text-gray-600 mb-2">{appointment.description}</p>
                            )}
                            {appointment.location && (
                              <div className="flex items-center gap-1 text-sm text-gray-500">
                                <MapPin className="w-3 h-3" />
                                {appointment.location}
                              </div>
                            )}
                          </div>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleDeleteAppointment(appointment.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="installments" className="space-y-6">
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Repeat className="w-5 h-5" />
                  Gastos Parcelados
                </CardTitle>
              </CardHeader>
              <CardContent>
                {installmentExpenses.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500 mb-4">Nenhum gasto parcelado registrado</p>
                    <p className="text-sm text-gray-400">Crie gastos parcelados para projetar despesas futuras!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {installmentExpenses.map((installment) => (
                      <div key={installment.id} className="p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <p className="font-medium text-gray-900">{installment.description}</p>
                            <Badge className={getCategoryColor(installment.category)}>
                              {installment.category}
                            </Badge>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-semibold text-gray-900">
                              {formatCurrency(installment.total_amount)}
                            </p>
                            <p className="text-sm text-gray-500">
                              {installment.installments}x de {formatCurrency(installment.monthly_amount)}
                            </p>
                          </div>
                        </div>
                        <p className="text-sm text-gray-500">
                          Criado em: {formatDate(installment.created_at)}
                        </p>
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

          <TabsContent value="reports" className="space-y-6">
            <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Relatório por Período
                </CardTitle>
                <CardDescription>
                  Selecione um período para gerar relatório detalhado
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Data Início</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button variant="outline" className="w-full justify-start text-left font-normal">
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {startDate ? format(startDate, "PPP", { locale: ptBR }) : "Selecione a data"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar mode="single" selected={startDate} onSelect={setStartDate} />
                      </PopoverContent>
                    </Popover>
                  </div>
                  
                  <div>
                    <Label>Data Fim</Label>
                    <Popover>
                      <PopoverTrigger asChild>
                        <Button variant="outline" className="w-full justify-start text-left font-normal">
                          <CalendarIcon className="mr-2 h-4 w-4" />
                          {endDate ? format(endDate, "PPP", { locale: ptBR }) : "Selecione a data"}
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar mode="single" selected={endDate} onSelect={setEndDate} />
                      </PopoverContent>
                    </Popover>
                  </div>
                </div>

                <div className="flex gap-4">
                  <Button onClick={loadPeriodReport} disabled={loading} className="flex-1">
                    {loading ? "Carregando..." : "Gerar Relatório"}
                  </Button>
                  <Button onClick={exportPDF} variant="outline" className="gap-2">
                    <Download className="w-4 h-4" />
                    Exportar PDF
                  </Button>
                </div>

                {periodReport && (
                  <div className="mt-6 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Card>
                        <CardContent className="pt-6">
                          <div className="text-2xl font-bold">{formatCurrency(periodReport.total_spent)}</div>
                          <p className="text-xs text-muted-foreground">Total Gasto</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-6">
                          <div className="text-2xl font-bold">{periodReport.total_expenses}</div>
                          <p className="text-xs text-muted-foreground">Número de Gastos</p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardContent className="pt-6">
                          <div className="text-2xl font-bold">{Object.keys(periodReport.categories).length}</div>
                          <p className="text-xs text-muted-foreground">Categorias</p>
                        </CardContent>
                      </Card>
                    </div>

                    <Card>
                      <CardHeader>
                        <CardTitle>Gastos do Período</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {periodReport.expenses.slice(0, 10).map((expense) => (
                            <div key={expense.id} className="flex justify-between items-center py-2 border-b">
                              <div>
                                <p className="font-medium">{expense.description}</p>
                                <p className="text-sm text-gray-500">{formatDate(expense.date)}</p>
                              </div>
                              <div className="text-right">
                                <p className="font-semibold">{formatCurrency(expense.amount)}</p>
                                <Badge className={getCategoryColor(expense.category)} size="sm">
                                  {expense.category}
                                </Badge>
                              </div>
                            </div>
                          ))}
                          {periodReport.expenses.length > 10 && (
                            <p className="text-sm text-gray-500 text-center pt-2">
                              E mais {periodReport.expenses.length - 10} gastos...
                            </p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;