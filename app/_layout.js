import { Stack } from "expo-router";
import { AuthProvider } from "../src/auth/AuthContext";

export default function Layout() {
  return (
    <AuthProvider>
      <Stack
        screenOptions={{
          headerShown: true,
        }}
      />
    </AuthProvider>
  );
}