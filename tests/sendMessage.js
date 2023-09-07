
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = {
        "provider": "64f94331c114d3a88b719304",
        "realm": {
            "connections": ["hello,world"],
            "action": "say.hello",
            "payload": "hello"
        }
    }

    const res = http.post('http://localhost:8000/messages', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
