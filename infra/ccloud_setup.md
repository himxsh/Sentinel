# ccloud CLI setup

1.  **Install `ccloud`**:
    ```bash
    brew install cockroachdb/tap/ccloud
    ```
    Or follow the [official get-started guide](https://www.cockroachlabs.com/docs/cockroachcloud/ccloud-get-started).

2.  **Authenticate** (interactive — opens browser):
    ```bash
    ccloud auth login
    ```

3.  **Headless / CI** — create a **Service Account** in Cloud Console
    (CockroachDB Cloud → Access → Service Accounts), assign **Viewer** role,
    then use the API key as a bearer token. See
    [official docs](https://www.cockroachlabs.com/docs/cockroachcloud/console-access-management#service-accounts).

4.  **Verify**:
    ```bash
    ccloud cluster list -o json
    ```

5.  **Sentinel `.env`** (optional):
    ```env
    CCLOUD_BIN=ccloud
    ```
    Defaults to `ccloud` on `PATH`; override if installed elsewhere.

> **Allow-list**: Sentinel only permits `cluster list` and `cluster info`. All other commands are rejected. Run destructive operations manually via Cloud Console.
