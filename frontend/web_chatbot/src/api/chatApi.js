export async function sendMessage(message) {
  // const res = await fetch("http://localhost:3001/api/chat", {
  //   method: "POST",
  //   headers: { "Content-Type": "application/json" },
  //   body: JSON.stringify({ message })
  // });

  // return res.json();
  return { reply: "res: " + message };
}
