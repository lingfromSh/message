
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = {
        "provider": "655ecfeff9d043dd4ea0b2a0",
        "realm": {
            "connections": ["01HFXCFEDEETWGVPAV5BD380J7", "01HFXCFD5HRC8QCX3B1EDH3C6K"],
            "action": "say.hello",
            "payload": "hello, shiyun.ling"
        }
    }

    const res = http.post('http://localhost:8080/messages', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
