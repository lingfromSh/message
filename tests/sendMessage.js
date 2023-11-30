
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = {
        "provider": "65674b3d76283f8b917bff96",
        "realm": {
            "connections": ["01HGDSJXRXCGJTCDK5C70B718A", "01HGDSJRNSPXVQ9REYDQY001N2"],
            "action": "say.hello",
            "payload": {
                "data": "shiyun"
            }
        }
    }

    const res = http.post('http://localhost:8080/messages', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
