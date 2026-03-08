import * as ImagePicker from "expo-image-picker";
import { View,Text } from "react-native";
import { API } from "../src/api/client";

export default function ScanWall(){

  async function scan(){

    const result = await ImagePicker.launchCameraAsync();

    if(result.canceled) return;

    const form = new FormData();

    form.append("file",{
      uri:result.assets[0].uri,
      type:"image/jpeg",
      name:"wall.jpg"
    })

    const response = await API.post(
      "/vision/wall/analyze",
      form,
      { headers:{ "Content-Type":"multipart/form-data"} }
    );

    console.log(response.data)
  }

  return(
    <View style={{padding:30}}>

      <Text style={{fontSize:28,fontWeight:"bold"}}>
        Scan Wall
      </Text>

      <Text onPress={scan} style={{marginTop:20}}>
        Take Photo
      </Text>

    </View>
  )
}