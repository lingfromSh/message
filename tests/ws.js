import { WebSocket } from 'k6/experimental/websockets';

export default function () {
    const ws = new WebSocket('ws://localhost:8080/websocket');
    ws.onopen = () => {
        ws.send(JSON.stringify({ "user_id": "studio:1" }));
        ws.close();
    };
}

