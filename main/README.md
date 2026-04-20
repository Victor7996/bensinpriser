# Bensinpriser - Home Assistant Integration

En Home Assistant-integration för att hämta bensinpriser från OKQ8 och andra källor i Sverige.

## Beskrivning

Denna integration hämtar bränslepriser från OKQ8:s API och använder henrikhjelm.se som fallback för äldre data. Den stödjer hela Sverige och kräver en OKQ8 API-nyckel.

## Funktioner

- Hämtar priser från OKQ8 API med pagination
- Fallback till henrikhjelm.se API om OKQ8-data saknas
- Stöd för miljövariabler för API-nyckel (.env-fil)
- Home Assistant config flow för enkel installation
- Sensorer för olika bränslen och stationer

## Installation

1. Kopiera `custom_components/bensinpriser/` till din Home Assistant `custom_components/` mapp.
2. Installera via HACS eller starta om Home Assistant.
3. Lägg till integrationen via Inställningar > Enheter & tjänster > Lägg till integration > Bensinpriser.

## Konfiguration

- **Lan**: Välj län (t.ex. Stockholm, Göteborg).
- **API-nyckel**: Ange OKQ8 subscription key eller använd .env-fil.

Skapa en `.env`-fil i projektroten med:
```
OKQ8_SUBSCRIPTION_KEY=din_nyckel_här
```

## API:er som används

- OKQ8 API: https://api.okq8.se/stationFuelProductPrices/v1/prices
- Fallback: https://henrikhjelm.se/api/getdata.php?lan={lan}

## Setup

Lägg till sensorer via integrations/dashboard i Home Assistant.

## Författare

Victor Lindholm (okq8 del)

## Referenser

- Original info: https://www.henrikhjelm.se/wordpress/bensin-priser-i-sverige-home-assistant/
- Automation av Janne Dannberg: https://pastebin.com/sDdEwWiA 
