import pytest

from services.library_service import (
    pay_late_fees,
    refund_late_fee_payment,
)
from services.payment_service import PaymentGateway

# ---------- pay_late_fees tests ----------

def test_pay_late_fees_success(mocker):
    # stub the late-fee lookup
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 5.00, "days_overdue": 2},
    )

    # stub book lookup
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 1, "title": "Test Book"},
    )

    # mock the gateway
    mock_gateway = mocker.Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_123", "OK")

    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)

    assert success is True
    assert "successful" in message.lower()
    assert txn_id == "txn_123"

    mock_gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=5.00,
        description="Late fees for 'Test Book'",
    )


def test_pay_late_fees_declined_by_gateway(mocker):
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 7.00, "days_overdue": 3},
    )
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 99, "title": "Another Book"},
    )

    mock_gateway = mocker.Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, "", "Payment declined")

    success, message, txn_id = pay_late_fees("123456", 99, mock_gateway)

    assert success is False
    assert "declined" in message.lower()
    assert txn_id is None

    mock_gateway.process_payment.assert_called_once()


def test_pay_late_fees_invalid_patron_id_does_not_call_gateway(mocker):
    # even if we stub fee/book, the function should fail first on patron_id
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 5.00, "days_overdue": 1},
    )
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 1, "title": "Test Book"},
    )

    mock_gateway = mocker.Mock(spec=PaymentGateway)

    success, message, txn_id = pay_late_fees("abc", 1, mock_gateway)

    assert success is False
    assert "invalid patron" in message.lower()
    assert txn_id is None

    # KEY requirement: mock not called
    mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_zero_fee_does_not_call_gateway(mocker):
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 0.0, "days_overdue": 0},
    )
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 1, "title": "Test Book"},
    )

    mock_gateway = mocker.Mock(spec=PaymentGateway)

    success, message, txn_id = pay_late_fees("123456", 1, mock_gateway)

    assert success is False
    assert "no late fees" in message.lower()
    assert txn_id is None

    mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_handles_gateway_exception(mocker):
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 4.5, "days_overdue": 1},
    )
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 2, "title": "Network Book"},
    )

    mock_gateway = mocker.Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = Exception("network error")

    success, message, txn_id = pay_late_fees("123456", 2, mock_gateway)

    assert success is False
    assert "error" in message.lower()
    assert txn_id is None

    mock_gateway.process_payment.assert_called_once()


# ---------- refund_late_fee_payment tests ----------

def test_refund_late_fee_payment_success(mocker):
    mock_gateway = mocker.Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "Refund OK")

    success, message = refund_late_fee_payment("txn_123456", 5.0, mock_gateway)

    assert success is True
    assert "refund ok".lower() in message.lower()

    mock_gateway.refund_payment.assert_called_once_with("txn_123456", 5.0)


def test_refund_late_fee_payment_invalid_txn_id(mocker):
    mock_gateway = mocker.Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("bad_id", 5.0, mock_gateway)

    assert success is False
    assert "invalid transaction" in message.lower()

    mock_gateway.refund_payment.assert_not_called()


@pytest.mark.parametrize("amount", [0, -1, 16.0])
def test_refund_late_fee_payment_invalid_amounts(mocker, amount):
    mock_gateway = mocker.Mock(spec=PaymentGateway)

    success, message = refund_late_fee_payment("txn_123456", amount, mock_gateway)

    assert success is False
    # it can be either "must be greater than 0" or "exceeds maximum late fee"
    assert "refund" in message.lower() or "amount" in message.lower()

    mock_gateway.refund_payment.assert_not_called()


def test_refund_late_fee_payment_gateway_exception(mocker):
    mock_gateway = mocker.Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = Exception("gateway down")

    success, message = refund_late_fee_payment("txn_123456", 5.0, mock_gateway)

    assert success is False
    assert "error" in message.lower()

    mock_gateway.refund_payment.assert_called_once_with("txn_123456", 5.0)
