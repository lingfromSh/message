
import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = {
        "query": "mutation createEndpoint {\n  createEndpoint(\n    input: {externalId: \"studio:2\", tags: [\"Flexiv\", \"Admin\"], websockets: [], emails: [\"lingfromsh@163.com\"]}\n  ) {\n    oid\n    externalId\n    tags\n    websockets\n    emails\n  }\n}",
        "operationName": "createEndpoint"
    }

    const res = http.post('http://localhost:8000/graphql', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
