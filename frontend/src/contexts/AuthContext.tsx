'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import {
  login as cognitoLogin,
  logout as cognitoLogout,
  getIdToken,
  getCurrentUsername,
  getCurrentSession,
} from '@/lib/cognito';
import { User } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const session = await getCurrentSession();
        if (session) {
          const username = getCurrentUsername();
          const idToken = session.getIdToken().getJwtToken();
          if (username && idToken) {
            setUser({ username, idToken });
          }
        }
      } catch {
        // Session invalid or expired
      } finally {
        setIsLoading(false);
      }
    };

    checkSession();
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const result = await cognitoLogin(username, password);
    if (result.success && result.idToken && result.username) {
      setUser({
        username: result.username,
        idToken: result.idToken,
      });
      return { success: true };
    }
    return { success: false, error: result.error };
  }, []);

  const logout = useCallback(() => {
    cognitoLogout();
    setUser(null);
  }, []);

  const getToken = useCallback(async () => {
    const token = await getIdToken();
    return token;
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        logout,
        getToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
