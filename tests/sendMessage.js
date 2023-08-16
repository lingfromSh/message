import { check } from 'k6';
import http from 'k6/http';

export default function () {

    // let data = {
    //     query: "mutation createPlan {\n    createPlan(\n        input: {\n            name: \"周五每1分钟发送一次消息\"\n            triggers: [\n                {\n                    type: REPEAT\n                    repeatAt: \"0-59/1 * * * 3-5\"\n                    repeatTime: -1\n                    startTime: \"2023-08-02T00:39:59+08:00\"\n                }\n            ]\n            subPlans: [\n                {\n                    provider: \"64d3877ce717ccfd2acb5abb\"\n                    message: {\n                        connections: [\"#etag:Admin\"]\n                        action: \"say.hello\"\n                        payload: \"hello\"\n                    }\n                }\n            ]\n            isEnabled: true\n        }\n    ) {\n        id\n        oid\n        name\n        subPlans {\n            provider {\n                oid\n                code\n                type\n            }\n            message\n        }\n        triggers {\n            type\n            repeatTime\n            repeatAt\n            timerAt\n            startTime\n            endTime\n        }\n        isEnabled\n        createdAt\n        updatedAt\n    }\n}\n",
    //     variables: {}
    // }

    let data = { "query": "mutation sendMessage {\n  sendMessage(\n    input: {provider: \"64db5b00778e603ca8c7888d\", realm: {connections: [\"#exid:studio:1\"], action: \"on.backup.recovery\", payload: \"01H6QT1TY610S2WPA4TVEY7Y98\"}}\n  ) {\n    provider {\n      oid\n      name\n      code\n      type\n    }\n    realm\n    status\n    createdAt\n    updatedAt\n  }\n}", "variables": {} }

    const res = http.post('http://10.18.0.90:9999/', JSON.stringify(data), {
        headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
        'is status 200': (r) => r.status === 200,
    });
}
