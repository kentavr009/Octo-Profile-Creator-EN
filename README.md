# Octo Browser Profile Creator

This script automatically creates profiles in Octo Browser in batch mode.

## Features

*   Creates profiles based on a proxy list from `proxies.csv`.
*   Cycles through the proxy list if more profiles need to be created than there are proxies.
*   (Optional) Sets cookies for each new profile from a `cookies.json` file.
*   Automatically generates a browser fingerprint using the Octo API.

## Setup

1.  Clone the repository:
    ```sh
    git clone https://github.com/YOUR_USERNAME/octo-profile-creator-en.git
    cd octo-profile-creator-en
    ```

2.  Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3.  Configure your environment variables. Copy the `.env.example` file to `.env`:
    ```sh
    cp .env.example .env
    ```
    Open the `.env` file and paste your `OCTO_API_TOKEN`.

4.  Prepare your data:
    *   Populate the `proxies.csv` file with your proxies. The header format must be: `type,host,port,login,password`.
    *   (Optional) If needed, add a `cookies.json` file. The keys in the JSON ("0", "1", etc.) correspond to the creation order of the profiles.

## Usage

Simply run the script:
```sh
python main.py
```By default, the script will create a number of profiles equal to the number of proxies in `proxies.csv`. To create a specific number of profiles, set the `PROFILE_COUNT` variable in your `.env` file.
