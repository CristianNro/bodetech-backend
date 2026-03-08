import { View, Text, Pressable } from "react-native";
import { router } from "expo-router";

export default function Home() {
  return (
    <View style={{ padding: 40 }}>
      <Text style={{ fontSize: 28, fontWeight: "bold" }}>
        BodeTech
      </Text>

      <Pressable onPress={() => router.push("/login")}>
        <Text style={{ marginTop: 20 }}>Login</Text>
      </Pressable>

      <Pressable onPress={() => router.push("/register")}>
        <Text style={{ marginTop: 20 }}>Crear cuenta</Text>
      </Pressable>
    </View>
  );
}