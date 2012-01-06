# We do this here to guarantee that es_utils gets imported and thus
# its request_finished signal handler is registered.
import search.es_utils
