import { check } from 'k6';
import http from 'k6/http';

export default function () {

    let data = { "query": "mutation sendMessage {\n  sendMessage(\n    input: {provider: \"64dc3ab71205772a1c895235\", realm: {connections: [\"#exid:studio:1\"], action: \"on.backup.recovery\", payload: \"01H6QT1TY610S2WPA4TVEY7Y98\"}}\n  ) {\n    provider {\n      oid\n      name\n      code\n      type\n    }\n    realm\n    status\n    createdAt\n    updatedAt\n  }\n}", "variables": {} }

    const res = http.post('http://localhost:8080/graphql', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
