import { useState } from "react";
import { View,Text } from "react-native";
import Input from "../src/ui/Input";
import Button from "../src/ui/Button";
import { API } from "../src/api/client";

export default function Chat(){

  const [msg,setMsg] = useState("");
  const [messages,setMessages] = useState([]);

  async function send(){

    const {data} = await API.post("/chat/message",{message:msg})

    setMessages([
      ...messages,
      {role:"user",text:msg},
      {role:"ai",text:data.answer}
    ])

    setMsg("")
  }

  return(
    <View style={{padding:30}}>

      {messages.map((m,i)=>(
        <Text key={i}>
          {m.role}: {m.text}
        </Text>
      ))}

      <Input value={msg} onChangeText={setMsg}/>
      <Button title="Send" onPress={send}/>

    </View>
  )
}