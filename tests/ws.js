import { sleep } from 'k6';
import { WebSocket } from 'k6/experimental/websockets';

export default function () {
    const ws = new WebSocket('ws://localhost:8080/websocket');
    ws.onopen = () => {
        ws.send("hello,world!");
        ws.close();
    };
}