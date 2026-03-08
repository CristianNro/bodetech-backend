import { useState, useContext } from "react";
import { View, Text } from "react-native";
import { router } from "expo-router";

import Input from "../src/ui/Input";
import Button from "../src/ui/Button";
import { AuthContext } from "../src/auth/AuthContext";

export default function Login() {

  const { login } = useContext(AuthContext);

  const [email,setEmail] = useState("");
  const [password,setPassword] = useState("");

  async function handleLogin(){
    await login(email,password);
    router.push("/cellars");
  }

  return (
    <View style={{padding:30}}>

      <Text style={{fontSize:28,fontWeight:"bold"}}>Login</Text>

      <Input placeholder="email" value={email} onChangeText={setEmail}/>
      <Input placeholder="password" value={password} onChangeText={setPassword} secureTextEntry/>

      <Button title="Login" onPress={handleLogin}/>

    </View>
  );
}