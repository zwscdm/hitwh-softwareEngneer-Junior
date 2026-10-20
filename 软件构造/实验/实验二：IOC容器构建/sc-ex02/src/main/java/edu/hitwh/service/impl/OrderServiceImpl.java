package edu.hitwh.service.impl;

import edu.hitwh.context.Component;
import edu.hitwh.repository.OrderRepo;
import edu.hitwh.service.OrderService;

import java.util.List;

@Component
public class OrderServiceImpl implements OrderService {

    private OrderRepo orderRepo;

    @Override
    public List<String> findAll() {
        return orderRepo.findAll();
    }
}
