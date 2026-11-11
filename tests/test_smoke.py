def test_package_is_importable():
    import cobrancas

    assert cobrancas.__doc__ == "Código do robô de cobrança."
