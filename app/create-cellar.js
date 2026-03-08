import { useState } from "react";
import { View,Text } from "react-native";
import { router } from "expo-router";
import AsyncStorage from "@react-native-async-storage/async-storage";

import Input from "../src/ui/Input";
import Button from "../src/ui/Button";
import { API } from "../src/api/client";

export default function CreateCellar(){

  const [name,setName] = useState("");

  async function create(){
    const token = await AsyncStorage.getItem("access_token");

    await API.post(
      "/cellars",
      { name },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    router.push("/cellars");
  }

  return(
    <View style={{padding:30}}>

      <Text style={{fontSize:28,fontWeight:"bold"}}>New Cellar</Text>

      <Input
      placeholder="cellar name"
      value={name}
      onChangeText={setName}
      />

      <Button title="Create" onPress={create}/>

    </View>
  )
}