
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = {
        "query": "mutation updateEndpoint {\n  updateEndpoint(input: {\n    externalId: \"studio:2\"\n  }){\n    oid\n    externalId\n    tags\n    websockets\n    emails\n  }\n}",
        "operationName": "updateEndpoint"
    }

    const res = http.post('http://localhost:8000/graphql', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
