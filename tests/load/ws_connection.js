import { sleep } from "k6";
import { WebSocket } from "k6/experimental/websockets";

export default function () {
  const ws = new WebSocket("ws://localhost:8000/");

  ws.onopen = () => {
    ws.close();
  };
}
