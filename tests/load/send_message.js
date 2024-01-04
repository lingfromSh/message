import http from "k6/http";

const url = "http://localhost:8000/graphql";

export default async function () {
  const data = {
    query:
      "fragment MessageNode on MessageTortoiseNode {\n  id\n  contacts\n  content\n  status\n  createdAt\n  updatedAt\n}\n\nquery Messages($users: [GlobalID!], $endpoints: [GlobalID!], $provider: [GlobalID!], $createdAtBefore: DateTime, $createdAtAfter: DateTime, $updatedAtBefore: DateTime, $updatedAtAfter: DateTime) {\n  messages(\n    provider: $provider\n    users: $users\n    endpoints: $endpoints\n    page: 1\n    pageSize: 100\n    createdAtBefore: $createdAtBefore\n    createdAtAfter: $createdAtAfter\n    updatedAtBefore: $updatedAtBefore\n    updatedAtAfter: $updatedAtAfter\n  ) {\n    pageInfo {\n      pageTotal\n      itemTotal\n      currentPage\n      currentPageSize\n    }\n    edges {\n      node {\n        ...MessageNode\n      }\n    }\n  }\n}\n\nmutation MessageSend($provider: GlobalID!, $users: [GlobalID!], $endpoints: [GlobalID!], $contacts: [JSON!], $message: JSON!) {\n  messageSend(\n    provider: $provider\n    users: $users\n    endpoints: $endpoints\n    contacts: $contacts\n    content: $message\n  ) \n}\n\nsubscription Message($id: GlobalID!, $interval: Int) {\n  message(id: $id, interval: $interval) {\n    ...MessageNode\n  }\n}",
    variables: {
      provider:
        "UHJvdmlkZXJUb3J0b2lzZU5vZGU6MDFIS0FDTVJFM0gyM1g3Vk5YN01QM1EwTUY=",
      message: {
        data: "hello,world",
        太棒了: "哈🙂哈哈哈",
      },
      users: ["VXNlclRvcnRvaXNlTm9kZTowMUhLQUU3SFpTVjBTVEFRQzlBQ1hQREcyOQ=="],
    },
    operationName: "MessageSend",
  };

  // Using a JSON string as body
  http.request("POST", url, JSON.stringify(data), {
    headers: { "Content-Type": "application/json" },
  });
}
