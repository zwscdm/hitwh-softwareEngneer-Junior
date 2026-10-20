package edu.hitwh.service.impl;

import edu.hitwh.context.Autowired;
import edu.hitwh.context.Component;
import edu.hitwh.repository.OrderRepo;
import edu.hitwh.service.OrderService;
import java.util.List;

@Component
public class OrderServiceImpl implements OrderService {
    @Autowired
    private OrderRepo orderRepo;

    public OrderRepo getOrderRepo() {
        return orderRepo;
    }

    public void setOrderRepo(OrderRepo orderRepo) {
        this.orderRepo = orderRepo;
    }

    @Override
    public List<String> findAll() {
        return orderRepo.findAll();
    }

    @Override
    public String toString() {
        return "OrderServiceImpl{" +
                "orderRepo=" + orderRepo +
                '}';
    }
}
