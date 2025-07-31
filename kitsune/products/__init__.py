from django.shortcuts import redirect

PRODUCT_SLUG_ALIASES = {
    "firefox-accounts": "mozilla-account",
    "firefox-private-network-vpn": "mozilla-vpn",
}


def get_product_redirect_response(product_slug, view_name, **kwargs):
    """
    Check if a product slug should be redirected and return the appropriate redirect response.

    Args:
        product_slug: The product slug to check
        view_name: The name of the view to redirect to
        **kwargs: Additional parameters to pass to the redirect
    Returns:
        HttpResponseRedirect if redirect is needed, None otherwise
    """

    if product_slug and product_slug in PRODUCT_SLUG_ALIASES:
        redirect_params = {
            "permanent": True,
        }

        if view_name.__name__ == "product_landing":
            redirect_params["slug"] = PRODUCT_SLUG_ALIASES[product_slug]
        else:
            redirect_params["product_slug"] = PRODUCT_SLUG_ALIASES[product_slug]

        # Only include kwargs that have actual values (not None)
        for key, value in kwargs.items():
            if value:
                redirect_params[key] = value

        return redirect(view_name, **redirect_params)

    return None
