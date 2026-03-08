import { TextInput } from "react-native";

export default function Input(props) {
  return (
    <TextInput
      {...props}
      style={{
        borderWidth: 1,
        borderColor: "#ddd",
        padding: 12,
        borderRadius: 10,
        marginTop: 10
      }}
    />
  );
}