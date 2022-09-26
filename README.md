# Crypto Marketdata Cloud Function
This is a repository of a cloud function to proxy requests to CoinGecko with caching and rate limits, for use in Google Sheets, etc. This prevents your requests from being blocked by the CoinGecko's CDN rate limits. This function code makes requests to the v3 API to obtain market data for all coin, but you can change the URL in the code for your use case. 

# GCP Setup
1. Mirror this repo (or a fork) to GCP Cloud Source ([docs](https://cloud.google.com/source-repositories/docs/mirroring-a-github-repository))
2. Setup a cloud function with HTTP trigger using the new GCP code repository
3. Setup the environmental variables `CACHE_TTL_SECS` and `WAIT_BETWEEN_CALLS_SECS` for the cloud function. Recommended values are `900` and `10` respectively.
4. Setup the cloud function with `concurrency` value of `1`, and maximum instances for scaling to `1`.
5. Setup a HTTP service with Cloud Run, to run the above function.
6. Optionally setup a custom domain for your service.
