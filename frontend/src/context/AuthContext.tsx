import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getStoredToken, setStoredToken } from "@/services/api";
import type { FarmerProfile } from "@/types";

interface AuthContextValue {
  farmer: FarmerProfile | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (identifier: string, password: string) => Promise<FarmerProfile>;
  register: (payload: Record<string, unknown>) => Promise<FarmerProfile>;
  refreshProfile: () => Promise<void>;
  updateProfile: (payload: Record<string, unknown>) => Promise<FarmerProfile>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [farmer, setFarmer] = useState<FarmerProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(getStoredToken()));

  const refreshProfile = useCallback(async () => {
    if (!getStoredToken()) {
      setFarmer(null);
      setLoading(false);
      return;
    }
    try {
      const profile = await api.getMyProfile();
      setFarmer(profile);
    } catch {
      setStoredToken(null);
      setFarmer(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshProfile();
  }, [refreshProfile]);

  const login = useCallback(async (identifier: string, password: string) => {
    const res = await api.login({ identifier, password });
    setStoredToken(res.access_token);
    setFarmer(res.farmer);
    return res.farmer;
  }, []);

  const register = useCallback(async (payload: Record<string, unknown>) => {
    const res = await api.register(payload);
    setStoredToken(res.access_token);
    setFarmer(res.farmer);
    return res.farmer;
  }, []);

  const updateProfile = useCallback(async (payload: Record<string, unknown>) => {
    const updated = await api.updateMyProfile(payload);
    setFarmer(updated);
    return updated;
  }, []);

  const logout = useCallback(() => {
    setStoredToken(null);
    setFarmer(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        farmer,
        loading,
        isAuthenticated: Boolean(farmer),
        login,
        register,
        refreshProfile,
        updateProfile,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}
