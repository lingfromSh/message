
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = {
        "name": "每分钟计划",
        "triggers": [
            {
                "type": "repeat",
                "repeat_at": "0-59/1 * * * *",
                "start_time": "2023-08-02T00:39:59+08:00",
                "repeat_time": 10
            }
        ],
        "sub_plans": [
            {
                "provider": "64f94331c114d3a88b719304",
                "message": {
                    "connections": ["exid:studio:1"],
                    "action": "say.hello",
                    "payload": "hello"
                }
            }
        ],
        "is_enabled": true
    }

    const res = http.post('http://localhost:8000/plans', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
