import { useState, useContext } from "react";
import { View, Text, Pressable } from "react-native";
import { router } from "expo-router";

import Input from "../src/ui/Input";
import Button from "../src/ui/Button";
import { AuthContext } from "../src/auth/AuthContext";

export default function Register(){

  const { register } = useContext(AuthContext);

  const [email,setEmail] = useState("");
  const [password,setPassword] = useState("");
  const [confirmPassword,setConfirmPassword] = useState("");

  const [showPassword,setShowPassword] = useState(false);
  const [error,setError] = useState("");

  function validateEmail(mail){
    return /\S+@\S+\.\S+/.test(mail);
  }

  async function handleRegister(){

    if(!validateEmail(email)){
      setError("Email inválido");
      return;
    }

    if(password.length < 8){
      setError("La contraseña debe tener mínimo 8 caracteres");
      return;
    }

    if(password !== confirmPassword){
      setError("Las contraseñas no coinciden");
      return;
    }

    setError("");

    try{
      await register(email,password);
      router.replace("/cellars");
    }catch(e){
      setError("Error creando la cuenta");
    }

  }

  return(
    <View style={{padding:30}}>

      <Text style={{fontSize:28,fontWeight:"bold"}}>
        Crear cuenta
      </Text>

      <Input
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
      />

      <Input
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry={!showPassword}
      />

      <Input
        placeholder="Confirm Password"
        value={confirmPassword}
        onChangeText={setConfirmPassword}
        secureTextEntry={!showPassword}
      />

      <Pressable onPress={()=>setShowPassword(!showPassword)}>
        <Text style={{marginTop:10}}>
          {showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
        </Text>
      </Pressable>

      {error !== "" && (
        <Text style={{
          color:"red",
          marginTop:12
        }}>
          {error}
        </Text>
      )}

      <Button
        title="Crear cuenta"
        onPress={handleRegister}
      />

      <Pressable onPress={()=>router.push("/login")}>
        <Text style={{marginTop:20}}>
          Ya tengo cuenta
        </Text>
      </Pressable>

    </View>
  )
}