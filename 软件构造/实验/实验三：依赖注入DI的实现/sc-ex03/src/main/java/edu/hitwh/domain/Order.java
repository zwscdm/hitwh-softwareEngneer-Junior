package edu.hitwh.domain;

import edu.hitwh.context.Autowired;
import edu.hitwh.context.Component;

@Component
public class Order {
    private Integer orderId;  // 订单id

    private Float amount;// 订单金额
    @Autowired
    private Account account;

    public Integer getOrderId() {
        return orderId;
    }

    public void setOrderId(Integer orderId) {
        this.orderId = orderId;
    }

    public Float getAmount() {
        return amount;
    }

    public void setAmount(Float amount) {
        this.amount = amount;
    }

    public Account getAccount() {
        return account;
    }

    public void setAccount(Account account) {
        this.account = account;
    }

    @Override
    public String toString() {
        return "Order{" +
                "orderId=" + orderId +
                ", amount=" + amount +
                ", account=" + account +
                '}';
    }
}
