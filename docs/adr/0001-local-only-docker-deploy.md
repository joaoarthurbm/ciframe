# Drop App Engine/Heroku legacy config in favor of a local-only Dockerfile

The project carried two dead deploy paths: `app.yaml` targeting Google App Engine's
`python27` runtime (discontinued; the modern App Engine Standard python3 runtimes use a
different `entrypoint`-based config and don't need `vendor.py`/`appengine_config.py`/`lib/`
vendoring at all) and a `Procfile` for Heroku. Neither was in active use — both prior
Heroku deployments (`ciframe-api.herokuapp.com`, `ciframe.herokuapp.com`) return 404.

We removed both and the App Engine vendoring artifacts, replacing them with a single
`Dockerfile` that runs the app locally via gunicorn. The backend itself keeps its existing
architecture (single `main.py`, in-memory CSV-backed search, Python 3.9) — only the
dependency versions (Flask, gunicorn) and the deploy mechanism changed.

Cloud deployment target is intentionally left undecided — Docker was chosen specifically
because it doesn't lock in a platform, so that decision can be made later without another
rewrite of the deploy config.
