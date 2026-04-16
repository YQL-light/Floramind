from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "plants" ADD "plantAvatar_url" VARCHAR(255) DEFAULT 'plantAvatars/default_avatar.png';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "plants" DROP COLUMN "plantAvatar_url";"""


MODELS_STATE = (
    "eJztW+1vmzgY/1cQn3pS1yMkBlKdTkpftvXWl6nL7qYdJ2TApNaISY29Lrfr/36yIeElJA"
    "ttQ8iULxGx/YD988Pz8vPDd3Uc+SiMjwaIYu9OPVa+qwSOkXqslHoOFRVOJlm7aGDQDeVQ"
    "mI1xY0ahx9RjJYBhjA4V1UexR/GE4YioxwrhYSgaIy9mFJNR1sQJvufIYdEIsTtE1WPl73"
    "8OFRUTH31D8ezv5IsTYBT6haliXzxbtjtsOpFtF4S9lgPF01zHi0I+JtngyZTdRWQ+GhMm"
    "WkeIIAoZErdnlIvpi9ml65ytKJlpNiSZYk7GRwHkIcstd00MvIgI/DBhYsHf1ZF4yiu90z"
    "N7VtfoWYeKKmcybzEfk+Vla08EJQLXQ/VR9kMGkxESxgy3r4jGYkoL4J3eQVqNXk6kBGHM"
    "aBnCGWCrMJw1ZCBmivNCKI7hNydEZMSEgusArMDsz8Ht6dvB7YEOwC9iNRGFXqLj12mXnv"
    "QJYDMgxatRA8R0+G4C2NG0NQDsaNpSAGVfEUAvIgwl72ARxD8+3FxXg5gTKQHpY48p/ykh"
    "jlk7AV2Bn1ivmPQ4ju/DPGwHV4NPZURPL29O5PqjmI2ovIu8wYn6+CiMZZAay7n1dKH35Q"
    "FS31noifRo2djFrrE+LrdAAkcSK7Fisb7UfXyMpSlfcCuyfaVT4TGicbt8ygkeLXUrYrrO"
    "7vmWvq53u6audQ0L9EwTWNrcySx2rfI2JxdvhMMpKOiPPZBATV7XsJ55mZcxoRvHumBAwT"
    "r2Eyw3n2DBeqIxxGEdCOcCu4jfRhzQ5C4itbRwLvAkCFOAthcFrQOhvhxBfRFAGMcPEfVr"
    "YZiT2c1gaDPR5FfIIHU4rfVOF6V2Uys3gWYYeVBMy/Ewm9YBdEFwJzHdiLUkEcMBTuGZUB"
    "QgioiH4jrx+6p7PCugbx7xJuL5QrZEkVi+AysSpjPIEMNjtCRpKkiWYU5Fj2YXLbXAFEH/"
    "hoTTdK9XoD+8uDr/MBxcvS9swdlgeC56dNk6LbUeGKVtmd9E+eti+FYRf5XPN9fn5Z2ajx"
    "t+VsWcIGeRQ6IHB/q5mGjWOgOmsLF84j9xY4uS+43d6samk88lk7HjoxAJsBeTyigKESRL"
    "yMqCYGlb3SgKN7WTdTPt9S3iyc3NZWHXTi5KaeP1x6uT89uDjtyu+D7ErJBNZrDGyOMUs6"
    "kDSfyQ8AnrOvcK0e26d9XmwPUMm/cC37d5HyBk877Vt2xuuqBnc8PqWTYPgg60uaFBy+aG"
    "qWk2B6Dv2dxwdd3mpmGJkX3Nt7mpG32bG4Ye2LyHPE38pncI1G0GZzWYqVx6EUIxq8W3J5"
    "V7/e4WhTKWqNjKlHN6L+7RTtOXIpu1VlkRH0OK0TNBOMOQTncMhE0SlIlSVDCUc21ZTlFm"
    "SrkbHKWc756krEtSEux9qUtS5mW2TG2oZY/QBTY3+4GmtoK8jCfIq7RqK5x3JrJ9bEHP6w"
    "g8Pb8deMqXfPAkCqlCtLGgKP/w+Ne03UlIraMJGantJplgzJwHyBCtCvFF6raEYyrJrUrc"
    "Go5Ge0gTkaard2xu+D3T5obXFdElQEDEnutGkSvAFplZCUiJheNNBejr13SUpH7s217KKJ"
    "iV1jaHFugZMlLvBAc2B329L7WqqdKPkoIGiDIc4n+foKNF0baqKXB9m1saBJtW0zkctVW1"
    "QrI5de1qlfqag601+opHd8yh6J5jisaoMvdbQd1XSjfny8bIx3ystve0jqHxRKyaU+RQSE"
    "a1YttK4ebA7VivdNBibPfs/E9B4u7Z+Z90Y/fsfDPsfK4ibkNldC15MRojqRaY8yLYi0i/"
    "jijCI/IOTSXaFyRmkHhV/rpUlrk75PCholL4MCdH8woUkfT1lOHM4MPp4OxcfVzntGHPtG"
    "+AaU/wqGDa50AtZ9pzG/JDqr3Md8pE0HJdTVyb4rdrIJsbUKSMwLTccobzpBs0SOMLMKZ7"
    "Gr8ujc8wC+vlOTOBrZ8MF1TQ0szkZFht/dcbQ/SN1f16YxvHIzl4QccSNIjr9p/NGw3PPw"
    "1X137No+DLm+s3s+HlgrBScajH8FdRuCDxqlMfWhbcvlb7XdfmQBe1DKZnimvTcpMaB8no"
    "YjI6VGaEmfyDmHfUjmOWBwSlna+xAzmR5tiSmBMinWtLv13IkUlP5KDaoctI79scIGjY3O"
    "pqXZsDI+gJXdY8QaRaeqLXhs01zdVOX3VAetUOdcZjOKpXv5tJNF6tq/4WcOIJ8BWX45Bh"
    "Eh+Jx/2uVh7QGgESsVzP/Hh7KexNx7S5ZRlr+s+mi3uT6G52krLuIU1R6pnnMxtzrqmLDQ"
    "CY16pt9JhmT8X+FIzdnor9STd2T8U2Q8XmC/82VS7YklejQaphT3Xvqe5WU90LJuAFYNvB"
    "IvrDEm55u1b3jODlCfLH/wFHzHz1"
)
