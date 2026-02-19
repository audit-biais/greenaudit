import { createContext, useContext, useState, useEffect } from 'react';
import api from './client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [partner, setPartner] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.get('/auth/me')
        .then((res) => setPartner(res.data))
        .catch(() => localStorage.removeItem('token'))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    localStorage.setItem('token', res.data.access_token);
    const me = await api.get('/auth/me');
    setPartner(me.data);
    return me.data;
  };

  const register = async (data) => {
    await api.post('/auth/register', data);
    return login(data.email, data.password);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setPartner(null);
  };

  return (
    <AuthContext.Provider value={{ partner, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
