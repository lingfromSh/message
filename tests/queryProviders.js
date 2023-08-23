import { check } from 'k6';
import http from 'k6/http';

export default function () {

    const res = http.get('http://localhost:8000/providers?page=&page_size=100&codes=&types=&names=', {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
