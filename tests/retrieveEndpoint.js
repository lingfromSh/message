import { check } from 'k6';
import http from 'k6/http';

export default function () {

    const res = http.get('http://localhost:8000/endpoint/studio:1', {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
