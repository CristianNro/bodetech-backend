import { useEffect,useState } from "react";
import { View,Text,Pressable } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { router } from "expo-router";
import { API } from "../src/api/client";

export default function Cellars(){

  const [cellars,setCellars] = useState([]);

  useEffect(()=>{
    load();
  },[])

  async function load(){
    const token = await AsyncStorage.getItem("access_token");

    const { data } = await API.get("/cellars", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    setCellars(data);
  }

  return(
    <View style={{padding:30}}>

      <Text style={{fontSize:28,fontWeight:"bold"}}>My Cellars</Text>

      {cellars.map(c=>(
        <Pressable
        key={c.cellar_id}
        onPress={()=>router.push(`/scan-wall?cellar=${c.cellar_id}`)}
        >
          <Text style={{marginTop:10,fontSize:18}}>
            {c.name}
          </Text>
        </Pressable>
      ))}

      <Pressable onPress={()=>router.push("/create-cellar")}>
        <Text style={{marginTop:20,fontWeight:"bold"}}>
          Create cellar
        </Text>
      </Pressable>

    </View>
  )
}