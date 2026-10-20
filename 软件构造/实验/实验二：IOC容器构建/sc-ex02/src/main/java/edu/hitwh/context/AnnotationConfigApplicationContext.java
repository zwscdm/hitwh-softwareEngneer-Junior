package edu.hitwh.context;

import edu.hitwh.utils.MyTools;

import java.lang.reflect.InvocationTargetException;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;


/**
 * 自定义框架的核心类
 */
public class AnnotationConfigApplicationContext {

    // 原材料集合：存放所有的标注有@Component的类的信息
    private Set<BeanDefination> beanDefinations = new HashSet<>();
    // ex02 新增部分：IOC 容器
    private Map<String, Object> singletonObjects = new ConcurrentHashMap<>();

    /**
     * 利用构造函数初始化。
     * 实验一：根据注解解决包扫描问题 ：Set<BeanDefination> findBeanDefinations(String packageToScan)
     * 实验二：根据原材料 beanDefinations 创建bean： void createObject(Set<BeanDefination> beanDefinations)
     * 实验三：实现对象的自动装配 autoWireObject(Set<BeanDefination> beanDefinations)
     * 实验四：将之上的三个方法重构，使其具有灵活性。
     *
     * @param packageToScan 待扫描的包
     */
    public AnnotationConfigApplicationContext(String packageToScan) throws InvocationTargetException, NoSuchMethodException, InstantiationException, IllegalAccessException {
        //exp01： 实验一：遍历 pageToScan，找到目标类
        beanDefinations = findBeanDefinations(packageToScan);
        //ex02：实验二：将 BeanDefinations 的信息取出，构建出 Bean容器
        createObject(beanDefinations);
    }


    /**
     * 找到所有classpath下标注了@Component的类的信息，并存储在一个集合中。
     * 算法思路：
     * 1. 利用工具类 MyTools.getgetClasses(String packageToScan) 获取packageToScan下所有的 .class文件，即形成所有的class对象，
     * 获得一个 classes 集合；注意：使用集合的主要原因是，集合中没有重复的值。
     * 2. 遍历classes集合，判断每一个class对象是否有@Component注解,获取所有标注@Component注解的class对象及其名字，
     * 存放到beanDefinations中，方便 实验2 中对其进行实例化。
     * <p>
     * 2.1 从集合中拿出一个class对象，假设命名为 clazz
     * 2.2 如果 class对象上有注解@Component,说明该class对象是我们自定义框架管理的Bean。那么就获取@Component的 value 属性，
     * 2.2.1 如果 value属性=“”，也就是value的默认值，那么，该 Bean 的名字应该是：不包括包的类名，并且要把类名首字母变小写。
     * 2.2.2 否则类名就是@Component注解的value值
     * 2.2.3 现在构建出BeanDefination对象，还缺scope值。因此，判断类名上有没有标注@Scope。
     * 如果有，拿到该scope注解对象后，获取其value的值，scope=该值；
     * 如果没有标注@Scope，那么就表示你的框架中，默认scope的值为“singleton”，表示该类为单例。
     * <p>
     * 2.2.4 现在，有了BeanName，有了Class对象，有了scope的值，因此可以产生一个BeanDefination对象，并且将该信息添加到 beanDefinations中。
     * 3. 返回 beanDefinations
     *
     * @param packageToScan 待扫描的包
     * @return 包下所有带 @Component注解的类的信息的集合
     */
    private Set<BeanDefination> findBeanDefinations(String packageToScan) {
        // 1. 获取包下的所有的类
        Set<Class<?>> classes = MyTools.getClasses(packageToScan);

        // 2. 遍历classes集合，判断是否有@Component注解
        for (Class<?> clazz : classes) {
            // 检查是否有@Component注解
            if (clazz.isAnnotationPresent(Component.class)) {
                // 获取@Component注解
                Component component = clazz.getAnnotation(Component.class);

                // 获取beanName
                String beanName;
                String value = component.value();

                // 判断value是否为空
                if (value == null || value.isEmpty()) {
                    // 获取简单类名（不包含包名）
                    String className = clazz.getSimpleName();
                    // 首字母小写
                    beanName = className.substring(0, 1).toLowerCase()
                            + className.substring(1);
                } else {
                    beanName = value;
                }

// 新增：获取scope值
                String scope = "singleton"; // 默认值
                if (clazz.isAnnotationPresent(Scope.class)) {
                    Scope scopeAnnotation = clazz.getAnnotation(Scope.class);
                    scope = scopeAnnotation.value();
                }

// 修改：创建BeanDefinition对象，传入scope参数
                BeanDefination bd = new BeanDefination(beanName, clazz, scope);
                // 添加到集合中
                beanDefinations.add(bd);

                // 可以打印日志（可选）
                System.out.println("找到Bean: " + beanName + " -> " + clazz.getName());
            }
        }

        return beanDefinations;
    }

    /**
     * 该私有方法的功能：遍历beanDefinations，取出每个beanDefination，根据其beanClass属性值，生成Bean对象，并将Bean对象放入单例池
     * <p>
     * 具体算法如下：
     * 1.获取beanDefinations的迭代器iterator
     * 2 利用iterator遍历beanDefinations集合
     * 2.1 取出集合中的一个 beanDefination对象。
     * 2.2 获取该对象的属性值 beanName、beanClass和 scope
     * 2.3 判断sope的值是否是“singleton”，如果是，将产生的对象放到单例池子。不是单例的不管。
     * 2.3.1 利用beanClass的 getDeclaredConstructor().newInstance()，获取Bean对象。
     * 2.3.2 将该Bean对象放入 singletonObjects 这个map<String,Object>中，String是指beanName，Object是指Bean对象。     *
     *
     * @param beanDefinations 所有标注了@Component注解的类的集合，又称为原材料集合。
     */
    private void createObject(Set<BeanDefination> beanDefinations) throws NoSuchMethodException, InvocationTargetException, InstantiationException, IllegalAccessException {
        // 1. 遍历所有图纸（BeanDefinition）
        for (BeanDefination bd : beanDefinations) {
            String beanName = bd.getBeanName();
            Class beanClass = bd.getBeanClass();
            String scope = bd.getScope();  // 从BeanDefinition中获取

            // 2. 检查是不是单例
            if ("singleton".equals(scope)) {
                // 3. 制造零件（创建对象）
                Object beanInstance = beanClass.getDeclaredConstructor().newInstance();

                // 4. 放入仓库（单例池）
                singletonObjects.put(beanName, beanInstance);
            }
            // 多例的现在不造，等需要时再造
        }
    }

    /**
     * 作用：根据 beanName，获得对象(不考虑 懒加载 )。
     * <p>
     * 算法描述：
     * 1. 根据入参 beanName 到singletonObjects中查。如果在 singletonObjects能查到，说明是单例，直接把查到的对象返回。
     * 2. 如果 singletonObjects中没有，说明不是单例（注意哈，不考虑懒加载的情况），需要遍历 BeanDefinations，找 beanName 对应
     * 的 Class 对象看是不是我们管理的bean。 如果是，临时产生一个对象返回，如果不是，说明beanName输错了或者压根不是我们框架管理的bean。
     * <p>
     * 具体步骤：
     * 2.1 如果能找到，产生一个对象就行返回就行。
     * 2.1.1 用 class对象的 getDeclaredConstructor().newInstance()产生 Bean 对象（此对象是多例的）
     * 2.1.2 return该对象，程序结束。
     * 2.2 如果找不到，说明入参 beanName写错了，或者压根不是 IoC容器管理的 Bean，直接抛出 NullPointerException,或者 return null。
     * 具体哪种方式，由你决定。
     *
     * @param beanName BeanDefinations中的存储的class对象的名字
     * @return 对象
     */
    public Object getBean(String beanName) throws NoSuchMethodException, InvocationTargetException, InstantiationException, IllegalAccessException {
        // 1. 先到单例仓库找
        if (singletonObjects.containsKey(beanName)) {
            return singletonObjects.get(beanName);  // 直接返回已有的
        }

        // 2. 单例仓库没有，可能是多例
        for (BeanDefination bd : beanDefinations) {
            if (beanName.equals(bd.getBeanName())) {
                // 找到图纸，临时造一个
                Class beanClass = bd.getBeanClass();
                return beanClass.getDeclaredConstructor().newInstance();
            }
        }

        // 3. 没找到图纸，说明beanName错了
        throw new NullPointerException("找不到Bean: " + beanName);
        // 或者 return null;
    }


    //=========以下是为了测试方便，临时添加的方法，勿动============================================

    /**
     * 获取所有的 Bean 信息，方便测试用。
     *
     * @return 集合
     */
    public Set<BeanDefination> getBeanDefinations() {
        return beanDefinations;
    }

    /**
     * 获取所有的 Bean，方便测试用。
     *
     * @return 单例池
     */
    public Map<String, Object> getSingletonObjects() {
        return singletonObjects;
    }
}
