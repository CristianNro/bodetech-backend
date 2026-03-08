import React, { createContext, useState } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { API } from "../api/client";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  async function login(email, password) {
    const { data } = await API.post("/auth/login", { email, password });

    console.log("Login response:", data);
    await AsyncStorage.setItem("token", data.access_token);
    await AsyncStorage.setItem("access_token", data.access_token);
    await AsyncStorage.setItem("refresh_token", data.refresh_token);
    console.log(data);
    setUser(data.user);
  }

  async function register(email, password) {
    const { data } = await API.post("/auth/register", { email, password, full_name: 'el bro' });

    await AsyncStorage.setItem("token", data.access_token);
    await AsyncStorage.setItem("access_token", data.access_token);
    await AsyncStorage.setItem("refresh_token", data.refresh_token);
    setUser(data.user);
  }

  async function logout() {
    await AsyncStorage.removeItem("token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}