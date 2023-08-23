
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = {
        "code": "websocket",
        "type": "websocket",
        "config": {},
        "name": "明关大段通外儿"
    }

    const res = http.post('http://localhost:8000/providers', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
