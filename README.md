# Quetzalito Sport — pruebas de APK sin publicidad

Repositorio independiente para probar modificaciones sobre **Quetzalito Sport 6.0**. No pertenece al proyecto BRENTEC TV.

## Estado
La compilación V5 es **experimental**: se ha verificado el parche binario y la integridad del DEX, pero **no se ha probado el inicio de la app ni la reproducción en Android**.

## Descargar
Cuando la automatización termine correctamente, el APK aparecerá en **Releases** de este repositorio. La primera publicación prevista se llama `QuetzalitoSport_V5_Prueba.apk`.

## Procedimiento
1. GitHub Actions descarga el APK de la página del desarrollador.
2. Verifica que su huella SHA-256 coincida con el original analizado.
3. Aplica un parche específico contra la apertura del anuncio `omg10.com`.
4. Firma y verifica el APK, luego lo publica en Releases.

La firma digital del APK modificado es diferente a la del original; respalda los datos de la aplicación antes de reemplazarla.

**No introduzcas contraseñas ni datos personales en esta app modificada.**
