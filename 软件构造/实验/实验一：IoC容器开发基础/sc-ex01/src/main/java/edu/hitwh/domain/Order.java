package edu.hitwh.domain;


import edu.hitwh.context.Component;

@Component
public class Order {
    private Integer orderId;  // 订单id
    private Float amount;// 订单金额

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
}
