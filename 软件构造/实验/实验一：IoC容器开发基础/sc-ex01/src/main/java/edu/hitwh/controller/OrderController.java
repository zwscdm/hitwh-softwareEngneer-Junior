package edu.hitwh.controller;


import edu.hitwh.context.Component;
import edu.hitwh.service.OrderService;

import java.util.List;

@Component
public class OrderController {
    private OrderService orderService;
    /**
     * 应该返回List<Order>,为了演示方便，暂时用String替换
     * @return
     */
    public List<String> getAllOrders(){
        return orderService.findAll();
    }
}
