from pushbulletrpc import pushbulletrpc


def ping():
    return "Pong", ":)"


def upper(data):
    return "Upper", data.upper()


if __name__ == "__main__":
    api_key = ""
    pb_rpc = pushbulletrpc.PushbulletRPC(api_key, "cli")
    print "PushBulletRPC started."
    pb_rpc.register_function(ping)
    pb_rpc.register_function(upper)
    try:
        pb_rpc.start()
    except KeyboardInterrupt:
        print "\nKeyboardInterrupt, exiting."
