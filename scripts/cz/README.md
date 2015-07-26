# Czech Address Data

## Downloading

1. visit [this link](http://vdp.cuzk.cz/vdp/ruian/vymennyformat/vyhledej?vf.pu=S&_vf.pu=on&_vf.pu=on&vf.cr=U&vf.up=OB&vf.ds=Z&vf.vu=Z&_vf.vu=on&_vf.vu=on&_vf.vu=on&_vf.vu=on&vf.uo=O&ob.kod=531723&search=Vyhledat)
2. fill out the form [this way](image.png)
3. click on 'Seznam linků'
4. download the URLs (I like to use `aria2c` for this). Place .gz files in a subdirectory called `data`
5. use the Makefile (`make process`) to process the results. It takes a while.
6. combine the results with `make combine`
7. `make upload`
8. update source JSON
