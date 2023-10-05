import argparse
import json
from datetime import datetime, timedelta

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()


class MagnumDestinationMonitor:
    def __init__(self, **kwargs):
        self.magnum = "127.0.0.1"
        self.client_id = "insite-poller"
        self.secret = ""
        self.tags = []
        self.nameset = "Global"
        self.nameset_id = None

        for key, value in kwargs.items():
            if "magnum" in key and value:
                self.magnum = value
            if "client_id" in key and value:
                self.client_id = value
            if "secret" in key and value:
                self.secret = value
            if "tags" in key and value:
                self.tags = value
            if "nameset" in key and value:
                self.nameset = value
            if "nameset_id" in key and value:
                self.nameset_id = value

        self.access_token_request = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.secret,
        }

        self.auth_url = (
            "https://%s/auth/realms/magnum/protocol/openid-connect/token" % self.magnum
        )
        self.graphql_url = "https://%s/graphql/v1.1" % self.magnum

        self.headers = {"Content-type": "application/json"}
        self.cookies = {}
        self.cookie_expiry = None

        if not self.nameset_id:
            self.nameset_id = self.find_nameset_id()

    @property
    def cookie_expired(self):
        if not self.cookie_expiry:
            return True

        now = self.cookie_expiry - datetime.now()

        if now.total_seconds() > 45:
            return False

        return True

    def auth(self):
        try:
            resp = requests.post(
                self.auth_url, data=self.access_token_request, verify=False, timeout=5
            )
            auth_data = json.loads(resp.text)

            if "error" in auth_data.keys():
                raise RuntimeError(
                    "%s %s" % (auth_data["error"], auth_data["error_description"])
                )

            self.cookies = {"magoidc-token": auth_data["access_token"]}
            self.cookie_expiry = datetime.now() + timedelta(0, auth_data["expires_in"])

            return True
        except Exception as err:
            print(err)

        return None

    def find_nameset_id(self):
        query = """
            query NAMESETS{
                namesets {
                    id name
                }
            }
        """

        if self.auth() and not self.cookie_expired:
            try:
                resp = requests.post(
                    self.graphql_url,
                    json={"query": query, "operationName": "NAMESETS"},
                    headers=self.headers,
                    cookies=self.cookies,
                    verify=False,
                    timeout=5,
                )

                nameset_resp = json.loads(resp.text)

                if "errors" in nameset_resp.keys():
                    raise RuntimeError(json.dumps(nameset_resp))

                if (
                    "data" in nameset_resp.keys()
                    and len(nameset_resp["data"]["namesets"]) > 0
                ):
                    for nameset in nameset_resp["data"]["namesets"]:
                        if nameset["name"] == self.nameset:
                            return nameset["id"]

                    raise RuntimeError("Error: couldn't find any nameset to match")
            except Exception as err:
                print(err)

            return None

    def fetch_destinations(self):
        query = """
            query physicalDestinationLikeTerminals($nameset: ID!, $path: String!, $tag: String!) {
                physicalDestinationLikeTerminals(input: {filters: [{ id: $path, value: $tag }]}) {
                    totalCount
                    edges(limit: 100) {
                        id name tags
                        routedPhysicalSource {
                            id name
                            resolvedName(namesetId: $nameset) { name }
                        }
                        namesetNames { name nameset { name } }
                    }
                }
            }
        """

        variables = {"nameset": self.nameset_id, "path": "tags", "tag": self.tags[-1]}
        operation_name = "physicalDestinationLikeTerminals"

        try:
            resp = requests.post(
                self.graphql_url,
                json={
                    "query": query,
                    "variables": variables,
                    "operationName": operation_name,
                },
                headers=self.headers,
                cookies=self.cookies,
                verify=False,
                timeout=15,
            )

            resp_data = json.loads(resp.text)

            if "errors" in resp_data.keys():
                raise RuntimeError(json.dumps(resp_data))

            if "data" in resp_data.keys():
                return resp_data["data"]

        except Exception as err:
            print(err)

        return None

    def collect(self):
        documents = []

        retry = 0
        while retry < 2 and self.cookie_expired:
            if self.auth():
                break
            retry += 1

        if self.cookie_expired:
            print("Failed to get a working cookie")
            return documents

        destinations = self.fetch_destinations()

        if not destinations:
            return documents

        for dest in destinations["physicalDestinationLikeTerminals"]["edges"]:
            fields = {
                "s_dest_id": dest.get("id"),
                "s_dest_name": dest.get("name"),
                "as_tags": dest.get("tags"),
                "s_src_name": None,
                "s_src_id": None,
                "s_src_name_resolved": None,
                "s_src_name_nameset": None,
            }

            for nameset in dest["namesetNames"]:
                fname = "s_" + nameset["nameset"]["name"].lower().replace(" ", "_")
                fields.update({fname: nameset["name"]})

            if dest["routedPhysicalSource"]:
                fields["s_src_name"] = dest["routedPhysicalSource"].get("name")
                fields["s_src_id"] = dest["routedPhysicalSource"].get("id")

                if dest["routedPhysicalSource"]["resolvedName"]:
                    fields["s_src_name_resolved"] = dest["routedPhysicalSource"][
                        "resolvedName"
                    ].get("name")
                    fields["s_src_name_nameset"] = self.nameset

            document = {"fields": fields, "host": self.magnum, "name": "dst_mon"}

            documents.append(document)

        return documents


def main():
    args_parser = argparse.ArgumentParser(description="Magnum Destination Poller")

    args_parser.add_argument(
        "-host",
        "--magnum-host",
        required=True,
        type=str,
        metavar="<ip>",
        help="Magnum IP Address",
    )

    args_parser.add_argument(
        "-client",
        "--client-id",
        required=False,
        type=str,
        default="insite-poller",
        metavar="<client-id>",
        help="Client ID in Magnum OIDC Credentials (default: 'insite-poller')",
    )

    args_parser.add_argument(
        "-secret",
        "--secret-key",
        required=True,
        type=str,
        metavar="<secret>",
        help="Secret Key from the Magnum OIDC Credentials",
    )

    args_parser.add_argument(
        "-name",
        "--nameset-name",
        required=False,
        type=str,
        default="Global",
        metavar="<nameset>",
        help="Nameset used to get the source label from (default: 'Global')",
    )

    args_parser.add_argument(
        "-t",
        "--tags",
        required=True,
        nargs="+",
        metavar="ENC-NOC TOC-NOC",
        help="Tags used to match destinations",
    )

    args = args_parser.parse_args()

    params = {
        "magnum": args.magnum_host,
        "client_id": args.client_id,
        "secret": args.secret_key,
        "tags": args.tags,
        "nameset": args.nameset_name,
    }

    magnum = MagnumDestinationMonitor(**params)

    magnum.fetch_destinations()

    q = ""
    while q.lower() != "q":
        # print(len(magnum.collect()))
        for count, doc in enumerate(magnum.collect(), 1):
            print(count, doc)

        q = input("Enter 'q' to quit, or just hit Enter: ")


if __name__ == "__main__":
    main()
