import { Pressable, Text } from "react-native";

export default function Button({ title, onPress }) {
  return (
    <Pressable
      onPress={onPress}
      style={{
        backgroundColor: "#111",
        padding: 12,
        borderRadius: 10,
        marginTop: 10
      }}
    >
      <Text style={{ color: "white", textAlign: "center", fontWeight: "bold" }}>
        {title}
      </Text>
    </Pressable>
  );
}