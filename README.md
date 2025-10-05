# Mumbleverse

Multiple Mumbles, one auth, not authenticator? What is this madnes!

# Mumble Server setup

1. shutdown authenticator if you are using it and reboot mumble.
1. Install and configure Mumble-auth-rest on your server
1. Add an API key and save the key you'll d it later

# Service Setup in Auth

1. install `pip install git+https://...`
1. add `"mumbleserver",` to `local.py`
1. migrate/collect status
1. restart auth
1. add mumble server via `admin > mumbleverse server` dont forget the key from above.
1. restart auth
1. add users job done

# External Credits

Built using this lovely [example plugin app](https://github.com/ppfeufer/aa-example-plugin#) for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth)
